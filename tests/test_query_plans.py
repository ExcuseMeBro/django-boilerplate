"""Synthetic PostgreSQL plans; never runs against or modifies application data.

pytest-django creates a test database and rolls back each dataset. Run with -s to
see JSON artifact paths. Latency is evidence, not a flaky cross-machine assertion.
"""
import json
from statistics import median
from time import perf_counter

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from test_messaging_queries import seed_rooms

pytestmark = pytest.mark.django_db


def summarize_node(node):
    keys = (
        'Node Type', 'Relation Name', 'Index Name', 'Plan Rows', 'Actual Rows',
        'Actual Loops', 'Actual Total Time', 'Shared Hit Blocks', 'Shared Read Blocks',
        'Sort Method', 'Sort Space Used', 'Sort Space Type',
    )
    result = {key: node[key] for key in keys if key in node}
    if 'Plans' in node:
        result['Plans'] = [summarize_node(child) for child in node['Plans']]
    return result


@pytest.mark.parametrize(('rooms', 'per_room'), [(5, 10), (1000, 20)])
def test_synthetic_query_plans(api, users, rooms, per_room, tmp_path):
    assert connection.vendor == 'postgresql', 'Query evidence requires Docker PostgreSQL, not SQLite'
    seed_rooms(users, rooms, per_room)
    with connection.cursor() as cursor:
        # Fixed identifiers, no caller-controlled SQL. Refresh stats after bulk seed.
        for table in ('users', 'conversations', 'conversations_participants', 'messages'):
            cursor.execute(f'ANALYZE {table}')
        cursor.execute('SHOW server_version')
        version = cursor.fetchone()[0]
    api.force_authenticate(users[0])
    report = {'postgresql': version, 'rooms': rooms, 'messages': rooms * per_room, 'endpoints': {}}
    for endpoint, budget in [('conversations', 4), ('messages', 2)]:
        url = f'/api/v1/{endpoint}/'
        assert api.get(url).status_code == 200  # warm URL resolver, connection, caches
        durations = []
        for _ in range(5):
            start = perf_counter()
            with CaptureQueriesContext(connection) as queries:
                response = api.get(url)
            durations.append((perf_counter() - start) * 1000)
            assert response.status_code == 200
            assert len(queries) == budget
            assert response.data['count'] == (rooms if endpoint == 'conversations' else rooms * per_room)
            assert len(response.data['results']) == min(20, response.data['count'])
        plans = []
        with connection.cursor() as cursor:
            for query in queries:
                # Only ORM-generated SELECT statements from this synthetic GET.
                assert query['sql'].lstrip().upper().startswith('SELECT')
                cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' + query['sql'])
                plan = cursor.fetchone()[0][0]
                plans.append({
                    'planning_ms': plan['Planning Time'], 'execution_ms': plan['Execution Time'],
                    'plan': summarize_node(plan['Plan']),
                })
        report['endpoints'][endpoint] = {
            'queries': len(queries), 'samples_ms': durations, 'median_ms': median(durations), 'plans': plans,
        }
    destination = tmp_path / f'query-plans-{rooms}.json'
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Query plan evidence: {destination}')
