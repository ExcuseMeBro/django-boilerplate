# 📋 TODO

## Commit 2 — authz + migration
- [ ] 🔴 🔨 Conversation.created_by FK + migration; perform_destroy/update owner-only
- [ ] 🔴 🔨 ConversationSerializer: participants read_only + add/remove action
- [ ] 🟠 🔨 DeviceTokenView: scope update_or_create by (user, token)
- [ ] 🟠 🔨 JWT blacklist app + BLACKLIST_AFTER_ROTATION + logout endpoint
- [ ] 🟡 🔨 Message.conversation -> read_only_fields

## Commit 3 — refactor + perf
- [ ] 🟠 🔨 ConversationViewSet N+1: prefetch participants + latest message
- [ ] 🟠 🔨 AppConfigView: stop creating row on GET
- [ ] 🟠 🔨 DeviceTokenView: move update_or_create into serializer.create()
- [ ] 🟡 🔨 Notification + Message composite indexes
- [ ] 🟡 🔨 normalize_phone() helper; NotificationQuerySet.for_user()
- [ ] 🟡 🔨 Avatar max size + dimension validators
- [ ] 🟢 🔨 Delete no-op localized_exception_handler
- [ ] 🟢 🔨 User.role: wire to permission class or drop

## Later
- [ ] 🟠 🧪 Tests: OTP send/verify, JWT, IDOR guards, throttle
