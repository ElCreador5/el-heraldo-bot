# Inventario de superficies de El Heraldo

Generado por `python tools/audit_inventory.py`. Las líneas corresponden al código de esta rama.
Incluye todas las definiciones y sitios dinámicos en INVENTARIO.json. Una referencia de prueba no acredita cobertura ni ejecución en Discord.

| Archivo:línea | Símbolo | Tipo |
| --- | --- | --- |
| bot.py:1336 | `pending_join_roles_loop` | scheduled_loop |
| bot.py:1413 | `join_roles_sync_loop` | scheduled_loop |
| bot.py:1951 | `on_ready` | event |
| bot.py:2116 | `on_guild_join` | event |
| bot.py:2153 | `on_member_join` | event |
| bot.py:2219 | `on_raw_message_delete` | event |
| bot.py:2251 | `heraldo_member_departure` | event |
| bot.py:2276 | `on_member_update` | event |
| bot.py:2454 | `check_pending_verifications` | scheduled_loop |
| bot.py:2702 | `HeraldoGeneralConfigModal` | view_or_modal |
| bot.py:2729 | `HeraldoGeneralConfigModal.on_submit` | interaction_hook |
| bot.py:2938 | `HeraldoChannelSetupView` | view_or_modal |
| bot.py:2991 | `HeraldoChannelSetupView.interaction_check` | interaction_hook |
| bot.py:3155 | `HeraldoRoleSetupView` | view_or_modal |
| bot.py:3186 | `HeraldoRoleSetupView.interaction_check` | interaction_hook |
| bot.py:3292 | `HeraldoRoleSetupView.save_changes` | component_callback |
| bot.py:3309 | `HeraldoRoleSetupView.discard_changes` | component_callback |
| bot.py:3317 | `HeraldoRoleSetupView.back` | component_callback |
| bot.py:3321 | `JoinRolesDelayModal` | view_or_modal |
| bot.py:3335 | `JoinRolesDelayModal.on_submit` | interaction_hook |
| bot.py:3352 | `JoinRolesScheduleModal` | view_or_modal |
| bot.py:3365 | `JoinRolesScheduleModal.on_submit` | interaction_hook |
| bot.py:3387 | `_JoinRolesOwnedView` | view_or_modal |
| bot.py:3393 | `_JoinRolesOwnedView.interaction_check` | interaction_hook |
| bot.py:3404 | `HeraldoJoinRolesSetupView` | view_or_modal |
| bot.py:3406 | `HeraldoJoinRolesSetupView.basic` | component_callback |
| bot.py:3414 | `HeraldoJoinRolesSetupView.users` | component_callback |
| bot.py:3422 | `HeraldoJoinRolesSetupView.bots` | component_callback |
| bot.py:3430 | `HeraldoJoinRolesSetupView.synchronization` | component_callback |
| bot.py:3438 | `HeraldoJoinRolesSetupView.back` | component_callback |
| bot.py:3449 | `JoinRolesCreateRoleModal` | view_or_modal |
| bot.py:3456 | `JoinRolesCreateRoleModal.on_submit` | interaction_hook |
| bot.py:3498 | `HeraldoJoinRolesBasicView` | view_or_modal |
| bot.py:3516 | `HeraldoJoinRolesBasicView.create_role` | component_callback |
| bot.py:3552 | `HeraldoJoinRolesBasicView.screening` | component_callback |
| bot.py:3563 | `HeraldoJoinRolesBasicView.delay` | component_callback |
| bot.py:3567 | `HeraldoJoinRolesBasicView.enable` | component_callback |
| bot.py:3581 | `HeraldoJoinRolesBasicView.disable` | component_callback |
| bot.py:3591 | `HeraldoJoinRolesBasicView.save_changes` | component_callback |
| bot.py:3617 | `HeraldoJoinRolesBasicView.discard_changes` | component_callback |
| bot.py:3629 | `HeraldoJoinRolesBasicView.back` | component_callback |
| bot.py:3636 | `JoinRolesUserIdModal` | view_or_modal |
| bot.py:3650 | `JoinRolesUserIdModal.on_submit` | interaction_hook |
| bot.py:3669 | `HeraldoJoinRolesUsersView` | view_or_modal |
| bot.py:3686 | `HeraldoJoinRolesUsersView.create_role` | component_callback |
| bot.py:3706 | `HeraldoJoinRolesUsersView.set_user_id` | component_callback |
| bot.py:3715 | `HeraldoJoinRolesUsersView.save_user` | component_callback |
| bot.py:3732 | `HeraldoJoinRolesUsersView.remove_user` | component_callback |
| bot.py:3744 | `HeraldoJoinRolesUsersView.remove_after` | component_callback |
| bot.py:3750 | `HeraldoJoinRolesUsersView.save_changes` | component_callback |
| bot.py:3759 | `HeraldoJoinRolesUsersView.discard_changes` | component_callback |
| bot.py:3767 | `HeraldoJoinRolesUsersView.back` | component_callback |
| bot.py:3774 | `HeraldoJoinRolesBotsView` | view_or_modal |
| bot.py:3792 | `HeraldoJoinRolesBotsView.create_role` | component_callback |
| bot.py:3824 | `HeraldoJoinRolesBotsView.bot_enabled` | component_callback |
| bot.py:3830 | `HeraldoJoinRolesBotsView.bot_delay` | component_callback |
| bot.py:3836 | `HeraldoJoinRolesBotsView.bot_different` | component_callback |
| bot.py:3847 | `HeraldoJoinRolesBotsView.save_changes` | component_callback |
| bot.py:3865 | `HeraldoJoinRolesBotsView.discard_changes` | component_callback |
| bot.py:3871 | `HeraldoJoinRolesBotsView.back` | component_callback |
| bot.py:3879 | `HeraldoJoinRolesSyncView` | view_or_modal |
| bot.py:3904 | `HeraldoJoinRolesSyncView.sync_now` | component_callback |
| bot.py:3916 | `HeraldoJoinRolesSyncView.schedule` | component_callback |
| bot.py:3920 | `HeraldoJoinRolesSyncView.save_changes` | component_callback |
| bot.py:3932 | `HeraldoJoinRolesSyncView.discard_changes` | component_callback |
| bot.py:3937 | `HeraldoJoinRolesSyncView.back` | component_callback |
| bot.py:3944 | `OrientationEmbedModal` | view_or_modal |
| bot.py:3982 | `OrientationEmbedModal.on_submit` | interaction_hook |
| bot.py:4006 | `HeraldoOrientationSetupView` | view_or_modal |
| bot.py:4034 | `HeraldoOrientationSetupView.interaction_check` | interaction_hook |
| bot.py:4105 | `HeraldoOrientationSetupView.activate` | component_callback |
| bot.py:4110 | `HeraldoOrientationSetupView.deactivate` | component_callback |
| bot.py:4115 | `HeraldoOrientationSetupView.edit_card` | component_callback |
| bot.py:4119 | `HeraldoOrientationSetupView.save_changes` | component_callback |
| bot.py:4175 | `HeraldoOrientationSetupView.discard_changes` | component_callback |
| bot.py:4182 | `HeraldoOrientationSetupView.back` | component_callback |
| bot.py:4187 | `orientation_reaction_add` | event |
| bot.py:4241 | `orientation_reaction_remove` | event |
| bot.py:4265 | `orientation_role_deleted` | event |
| bot.py:4297 | `orientation_message_deleted` | event |
| bot.py:4310 | `HeraldoMotwScheduleModal` | view_or_modal |
| bot.py:4328 | `HeraldoMotwScheduleModal.on_submit` | interaction_hook |
| bot.py:4346 | `HeraldoMotwSetupView` | view_or_modal |
| bot.py:4362 | `HeraldoMotwSetupView.interaction_check` | interaction_hook |
| bot.py:4397 | `HeraldoMotwSetupView.schedule` | component_callback |
| bot.py:4401 | `HeraldoMotwSetupView.test` | component_callback |
| bot.py:4410 | `HeraldoMotwSetupView.save_changes` | component_callback |
| bot.py:4419 | `HeraldoMotwSetupView.discard_changes` | component_callback |
| bot.py:4424 | `HeraldoMotwSetupView.back` | component_callback |
| bot.py:4429 | `HeraldoHoneypotSetupView` | view_or_modal |
| bot.py:4446 | `HeraldoHoneypotSetupView.interaction_check` | interaction_hook |
| bot.py:4477 | `HeraldoHoneypotSetupView.create_channel` | component_callback |
| bot.py:4524 | `HeraldoHoneypotSetupView.toggle` | component_callback |
| bot.py:4534 | `HeraldoHoneypotSetupView.edit_warning` | component_callback |
| bot.py:4538 | `HeraldoHoneypotSetupView.edit_text` | component_callback |
| bot.py:4542 | `HeraldoHoneypotSetupView.save_changes` | component_callback |
| bot.py:4560 | `HeraldoHoneypotSetupView.discard_changes` | component_callback |
| bot.py:4566 | `HeraldoHoneypotSetupView.back` | component_callback |
| bot.py:4626 | `HeraldoVerificationSetupView` | view_or_modal |
| bot.py:4664 | `HeraldoVerificationSetupView.interaction_check` | interaction_hook |
| bot.py:4734 | `HeraldoVerificationSetupView.create_verify_channel` | component_callback |
| bot.py:4771 | `HeraldoVerificationSetupView.create_verify_role` | component_callback |
| bot.py:4787 | `HeraldoVerificationSetupView.create_sin_role` | component_callback |
| bot.py:4803 | `HeraldoVerificationSetupView.texts` | component_callback |
| bot.py:4807 | `HeraldoVerificationSetupView.publish` | component_callback |
| bot.py:4849 | `HeraldoVerificationSetupView.toggle` | component_callback |
| bot.py:4860 | `HeraldoVerificationSetupView.save_changes` | component_callback |
| bot.py:4883 | `HeraldoVerificationSetupView.discard_changes` | component_callback |
| bot.py:4888 | `HeraldoVerificationSetupView.back` | component_callback |
| bot.py:4892 | `HeraldoRaidDetectionModal` | view_or_modal |
| bot.py:4934 | `HeraldoRaidDetectionModal.on_submit` | interaction_hook |
| bot.py:4965 | `HeraldoRaidSetupView` | view_or_modal |
| bot.py:5000 | `HeraldoRaidSetupView.interaction_check` | interaction_hook |
| bot.py:5041 | `HeraldoRaidSetupView.detection` | component_callback |
| bot.py:5045 | `HeraldoRaidSetupView.toggle_enabled` | component_callback |
| bot.py:5052 | `HeraldoRaidSetupView.toggle_invites` | component_callback |
| bot.py:5059 | `HeraldoRaidSetupView.toggle_purge` | component_callback |
| bot.py:5066 | `HeraldoRaidSetupView.save_changes` | component_callback |
| bot.py:5085 | `HeraldoRaidSetupView.discard_changes` | component_callback |
| bot.py:5090 | `HeraldoRaidSetupView.back` | component_callback |
| bot.py:5094 | `VerifyDmEditorContentModal` | view_or_modal |
| bot.py:5141 | `VerifyDmEditorContentModal.on_submit` | interaction_hook |
| bot.py:5167 | `VerifyDmEditorVisualModal` | view_or_modal |
| bot.py:5182 | `VerifyDmEditorVisualModal.on_submit` | interaction_hook |
| bot.py:5198 | `VerifyDmMessageSetupView` | view_or_modal |
| bot.py:5204 | `VerifyDmMessageSetupView.interaction_check` | interaction_hook |
| bot.py:5216 | `VerifyDmMessageSetupView.content` | component_callback |
| bot.py:5220 | `VerifyDmMessageSetupView.visual` | component_callback |
| bot.py:5224 | `VerifyDmMessageSetupView.preview` | component_callback |
| bot.py:5235 | `VerifyDmMessageSetupView.back` | component_callback |
| bot.py:5243 | `SuggestionPanelContentModal` | view_or_modal |
| bot.py:5270 | `SuggestionPanelContentModal.on_submit` | interaction_hook |
| bot.py:5290 | `SuggestionPanelVisualModal` | view_or_modal |
| bot.py:5328 | `SuggestionPanelVisualModal.on_submit` | interaction_hook |
| bot.py:5355 | `SuggestionPanelMessageSetupView` | view_or_modal |
| bot.py:5361 | `SuggestionPanelMessageSetupView.interaction_check` | interaction_hook |
| bot.py:5370 | `SuggestionPanelMessageSetupView.content` | component_callback |
| bot.py:5374 | `SuggestionPanelMessageSetupView.design` | component_callback |
| bot.py:5378 | `SuggestionPanelMessageSetupView.sync` | component_callback |
| bot.py:5387 | `SuggestionPanelMessageSetupView.back` | component_callback |
| bot.py:5494 | `DefaultMessageStudioView` | view_or_modal |
| bot.py:5548 | `DefaultMessageStudioView.interaction_check` | interaction_hook |
| bot.py:6043 | `LogTemplateResetConfirmView` | view_or_modal |
| bot.py:6049 | `LogTemplateResetConfirmView.interaction_check` | interaction_hook |
| bot.py:6059 | `LogTemplateResetConfirmView.confirm` | component_callback |
| bot.py:6065 | `LogTemplateResetConfirmView.cancel` | component_callback |
| bot.py:6070 | `LogTemplateSaveConfirmView` | view_or_modal |
| bot.py:6077 | `LogTemplateSaveConfirmView.interaction_check` | interaction_hook |
| bot.py:6087 | `LogTemplateSaveConfirmView.save` | component_callback |
| bot.py:6094 | `LogTemplateSaveConfirmView.cancel` | component_callback |
| bot.py:6099 | `LogTemplateContentModal` | view_or_modal |
| bot.py:6143 | `LogTemplateContentModal.on_submit` | interaction_hook |
| bot.py:6157 | `LogTemplateVisualModal` | view_or_modal |
| bot.py:6201 | `LogTemplateVisualModal.on_submit` | interaction_hook |
| bot.py:6305 | `LogTemplateEditorView` | view_or_modal |
| bot.py:6410 | `LogTemplateEditorView.interaction_check` | interaction_hook |
| bot.py:6544 | `HeraldoMessageConfirmView` | view_or_modal |
| bot.py:6560 | `HeraldoMessageConfirmView.interaction_check` | interaction_hook |
| bot.py:6569 | `HeraldoMessageConfirmView.commit` | component_callback |
| bot.py:6653 | `HeraldoMessageConfirmView.cancel` | component_callback |
| bot.py:6724 | `HeraldoTemplateModal` | view_or_modal |
| bot.py:6743 | `HeraldoTemplateModal.on_submit` | interaction_hook |
| bot.py:6788 | `HeraldoTemplateRawModal` | view_or_modal |
| bot.py:6797 | `HeraldoTemplateRawModal.on_submit` | interaction_hook |
| bot.py:6817 | `HeraldoTemplateSetupView` | view_or_modal |
| bot.py:6838 | `HeraldoTemplateSetupView.interaction_check` | interaction_hook |
| bot.py:6869 | `HeraldoTemplateSetupView.create` | component_callback |
| bot.py:6873 | `HeraldoTemplateSetupView.edit` | component_callback |
| bot.py:6880 | `HeraldoTemplateSetupView.attach` | component_callback |
| bot.py:6887 | `HeraldoTemplateSetupView.publish` | component_callback |
| bot.py:6910 | `HeraldoTemplateSetupView.edit_raw` | component_callback |
| bot.py:6922 | `HeraldoTemplateSetupView.variables` | component_callback |
| bot.py:6926 | `HeraldoTemplateSetupView.preview` | component_callback |
| bot.py:6941 | `HeraldoTemplateSetupView.delete` | component_callback |
| bot.py:6951 | `HeraldoTemplateSetupView.back` | component_callback |
| bot.py:6968 | `HeraldoMessageRoleModal` | view_or_modal |
| bot.py:6977 | `HeraldoMessageRoleModal.on_submit` | interaction_hook |
| bot.py:7004 | `HeraldoMessageComponentsSetupView` | view_or_modal |
| bot.py:7009 | `HeraldoMessageComponentsSetupView.interaction_check` | interaction_hook |
| bot.py:7018 | `HeraldoMessageComponentsSetupView.create` | component_callback |
| bot.py:7022 | `HeraldoMessageComponentsSetupView.list_components` | component_callback |
| bot.py:7028 | `HeraldoMessageComponentsSetupView.back` | component_callback |
| bot.py:7033 | `HeraldoAttachRoleModal` | view_or_modal |
| bot.py:7041 | `HeraldoAttachRoleModal.on_submit` | interaction_hook |
| bot.py:7140 | `heraldo_message_components_dispatch` | event |
| bot.py:7162 | `HeraldoMessageKitImportModal` | view_or_modal |
| bot.py:7169 | `HeraldoMessageKitImportModal.on_submit` | interaction_hook |
| bot.py:7196 | `HeraldoMessageKitsView` | view_or_modal |
| bot.py:7201 | `HeraldoMessageKitsView.interaction_check` | interaction_hook |
| bot.py:7210 | `HeraldoMessageKitsView.export` | component_callback |
| bot.py:7219 | `HeraldoMessageKitsView.import_kit` | component_callback |
| bot.py:7223 | `HeraldoMessageKitsView.back` | component_callback |
| bot.py:7228 | `HeraldoMessagesSetupView` | view_or_modal |
| bot.py:7259 | `HeraldoMessagesSetupView.interaction_check` | interaction_hook |
| bot.py:7372 | `HeraldoMessagesSetupView.back` | component_callback |
| bot.py:7429 | `ModerationReactionEditModal` | view_or_modal |
| bot.py:7442 | `ModerationReactionEditModal.on_submit` | interaction_hook |
| bot.py:7473 | `ModerationReactionRuleModal` | view_or_modal |
| bot.py:7491 | `ModerationReactionRuleModal.on_submit` | interaction_hook |
| bot.py:7550 | `ModerationCondemnEmojiModal` | view_or_modal |
| bot.py:7558 | `ModerationCondemnEmojiModal.on_submit` | interaction_hook |
| bot.py:7579 | `HeraldoUserReportsSetupView` | view_or_modal |
| bot.py:7599 | `HeraldoUserReportsSetupView.interaction_check` | interaction_hook |
| bot.py:7689 | `HeraldoUserReportsSetupView.add_reaction` | component_callback |
| bot.py:7696 | `HeraldoUserReportsSetupView.edit_reaction` | component_callback |
| bot.py:7703 | `HeraldoUserReportsSetupView.edit_rule` | component_callback |
| bot.py:7710 | `HeraldoUserReportsSetupView.delete_reaction` | component_callback |
| bot.py:7722 | `HeraldoUserReportsSetupView.edit_condemn_emoji` | component_callback |
| bot.py:7726 | `HeraldoUserReportsSetupView.save_changes` | component_callback |
| bot.py:7748 | `HeraldoUserReportsSetupView.discard_changes` | component_callback |
| bot.py:7757 | `HeraldoUserReportsSetupView.back` | component_callback |
| bot.py:7763 | `HeraldoCasesSetupView` | view_or_modal |
| bot.py:7769 | `HeraldoCasesSetupView.interaction_check` | interaction_hook |
| bot.py:7778 | `HeraldoCasesSetupView.refresh` | component_callback |
| bot.py:7782 | `HeraldoCasesSetupView.back` | component_callback |
| bot.py:7788 | `HeraldoCondemnationDurationModal` | view_or_modal |
| bot.py:7802 | `HeraldoCondemnationDurationModal.on_submit` | interaction_hook |
| bot.py:7818 | `HeraldoCondemnationSetupView` | view_or_modal |
| bot.py:7845 | `HeraldoCondemnationSetupView.interaction_check` | interaction_hook |
| bot.py:7903 | `HeraldoCondemnationSetupView.duration` | component_callback |
| bot.py:7907 | `HeraldoCondemnationSetupView.create_channel` | component_callback |
| bot.py:7944 | `HeraldoCondemnationSetupView.create_role` | component_callback |
| bot.py:7960 | `HeraldoCondemnationSetupView.save` | component_callback |
| bot.py:7975 | `HeraldoCondemnationSetupView.discard` | component_callback |
| bot.py:7980 | `HeraldoCondemnationSetupView.back` | component_callback |
| bot.py:7987 | `HeraldoModerationSetupView` | view_or_modal |
| bot.py:7993 | `HeraldoModerationSetupView.interaction_check` | interaction_hook |
| bot.py:8002 | `HeraldoModerationSetupView.condemnations` | component_callback |
| bot.py:8008 | `HeraldoModerationSetupView.cases` | component_callback |
| bot.py:8016 | `HeraldoModerationSetupView.user_reports` | component_callback |
| bot.py:8022 | `HeraldoModerationSetupView.back` | component_callback |
| bot.py:8027 | `HeraldoAutomodSetupView` | view_or_modal |
| bot.py:8033 | `HeraldoAutomodSetupView.interaction_check` | interaction_hook |
| bot.py:8042 | `HeraldoAutomodSetupView.honeypot` | component_callback |
| bot.py:8051 | `HeraldoAutomodSetupView.raid_protection` | component_callback |
| bot.py:8060 | `HeraldoAutomodSetupView.back` | component_callback |
| bot.py:8064 | `HeraldoVerificationHubView` | view_or_modal |
| bot.py:8070 | `HeraldoVerificationHubView.interaction_check` | interaction_hook |
| bot.py:8079 | `HeraldoVerificationHubView.age_verification` | component_callback |
| bot.py:8088 | `HeraldoVerificationHubView.preference_verification` | component_callback |
| bot.py:8097 | `HeraldoVerificationHubView.times` | component_callback |
| bot.py:8101 | `HeraldoVerificationHubView.back` | component_callback |
| bot.py:8105 | `HeraldoLoggingSetupView` | view_or_modal |
| bot.py:8121 | `HeraldoLoggingSetupView.interaction_check` | interaction_hook |
| bot.py:8161 | `HeraldoLoggingSetupView.create_channel` | component_callback |
| bot.py:8198 | `HeraldoLoggingSetupView.member_events` | component_callback |
| bot.py:8203 | `HeraldoLoggingSetupView.save` | component_callback |
| bot.py:8217 | `HeraldoLoggingSetupView.discard` | component_callback |
| bot.py:8222 | `HeraldoLoggingSetupView.back` | component_callback |
| bot.py:8239 | `HeraldoMemberLogSetupView` | view_or_modal |
| bot.py:8256 | `HeraldoMemberLogSetupView.interaction_check` | interaction_hook |
| bot.py:8300 | `HeraldoMemberLogSetupView.toggle` | component_callback |
| bot.py:8306 | `HeraldoMemberLogSetupView.save` | component_callback |
| bot.py:8328 | `HeraldoMemberLogSetupView.discard` | component_callback |
| bot.py:8333 | `HeraldoMemberLogSetupView.back` | component_callback |
| bot.py:8403 | `HeraldoReactionEmojiModal` | view_or_modal |
| bot.py:8410 | `HeraldoReactionEmojiModal.on_submit` | interaction_hook |
| bot.py:8436 | `HeraldoReactionOptionsModal` | view_or_modal |
| bot.py:8448 | `HeraldoReactionOptionsModal.on_submit` | interaction_hook |
| bot.py:8468 | `HeraldoReactionMessageModal` | view_or_modal |
| bot.py:8478 | `HeraldoReactionMessageModal.on_submit` | interaction_hook |
| bot.py:8492 | `HeraldoReactionRoleCreateModal` | view_or_modal |
| bot.py:8503 | `HeraldoReactionRoleCreateModal.on_submit` | interaction_hook |
| bot.py:8560 | `HeraldoReactionRolesEditorView` | view_or_modal |
| bot.py:8644 | `HeraldoReactionRolesEditorView.interaction_check` | interaction_hook |
| bot.py:8740 | `HeraldoReactionRolesEditorView.add_emoji` | component_callback |
| bot.py:8744 | `HeraldoReactionRolesEditorView.options` | component_callback |
| bot.py:8748 | `HeraldoReactionRolesEditorView.edit_message` | component_callback |
| bot.py:8755 | `HeraldoReactionRolesEditorView.save` | component_callback |
| bot.py:8822 | `HeraldoReactionRolesEditorView.back` | component_callback |
| bot.py:8827 | `HeraldoReactionExistingModal` | view_or_modal |
| bot.py:8834 | `HeraldoReactionExistingModal.on_submit` | interaction_hook |
| bot.py:8858 | `HeraldoReactionDeleteModal` | view_or_modal |
| bot.py:8865 | `HeraldoReactionDeleteModal.on_submit` | interaction_hook |
| bot.py:8896 | `HeraldoReactionRolesSetupView` | view_or_modal |
| bot.py:8920 | `HeraldoReactionRolesSetupView.interaction_check` | interaction_hook |
| bot.py:8954 | `HeraldoReactionRolesSetupView.create` | component_callback |
| bot.py:8966 | `HeraldoReactionRolesSetupView.existing` | component_callback |
| bot.py:8970 | `HeraldoReactionRolesSetupView.back` | component_callback |
| bot.py:9087 | `general_reaction_role_add` | event |
| bot.py:9092 | `general_reaction_role_remove` | event |
| bot.py:9096 | `HeraldoPendingSetupModuleView` | view_or_modal |
| bot.py:9103 | `HeraldoPendingSetupModuleView.interaction_check` | interaction_hook |
| bot.py:9112 | `HeraldoPendingSetupModuleView.back` | component_callback |
| bot.py:9116 | `HeraldoSetupView` | view_or_modal |
| bot.py:9156 | `HeraldoSetupView.interaction_check` | interaction_hook |
| bot.py:9229 | `HeraldoSetupView.on_error` | interaction_hook |
| bot.py:9253 | `HeraldoSetupView.close` | component_callback |
| bot.py:9263 | `heraldo_importkit` | command |
| bot.py:9297 | `heraldo_sendtemplate` | command |
| bot.py:9334 | `HeraldoEditTemplateConfirmView` | view_or_modal |
| bot.py:9341 | `HeraldoEditTemplateConfirmView.interaction_check` | interaction_hook |
| bot.py:9351 | `HeraldoEditTemplateConfirmView.confirm` | component_callback |
| bot.py:9384 | `HeraldoEditTemplateConfirmView.cancel` | component_callback |
| bot.py:9392 | `heraldo_edittemplate` | command |
| bot.py:9448 | `setup` | command |
| bot.py:9480 | `heraldo_check` | command |
| bot.py:9507 | `heraldo_check_all` | command |
| bot.py:9592 | `HeraldoLogChannelConfirmView` | view_or_modal |
| bot.py:9602 | `HeraldoLogChannelConfirmView.interaction_check` | interaction_hook |
| bot.py:9606 | `HeraldoLogChannelConfirmView.confirm` | component_callback |
| bot.py:9640 | `HeraldoLogChannelConfirmView.cancel` | component_callback |
| bot.py:9655 | `heraldo_log_channel` | command |
| bot.py:9705 | `VerifyView` | view_or_modal |
| bot.py:9978 | `VerifyTextsModal` | view_or_modal |
| bot.py:10005 | `VerifyTextsModal.on_submit` | interaction_hook |
| bot.py:10019 | `verify` | command |
| bot.py:10081 | `verify_dm_texts` | command |
| bot.py:10161 | `verify_dm_preview` | command |
| bot.py:10197 | `verify_texts` | command |
| bot.py:10215 | `verify_config` | command |
| bot.py:10339 | `joinroles_status` | command |
| bot.py:10353 | `joinroles_sync_command` | command |
| bot.py:10367 | `joinroles_add` | command |
| bot.py:10395 | `joinroles_remove` | command |
| bot.py:10415 | `joinroles_user_add` | command |
| bot.py:10446 | `joinroles_user_remove` | command |
| bot.py:10709 | `template_backup_loop` | scheduled_loop |
| bot.py:10759 | `template_config` | command |
| bot.py:10830 | `template_sync` | command |
| bot.py:10869 | `track_activity` | event |
| bot.py:10888 | `moderation_cache_recent_messages` | event |
| bot.py:10910 | `profile` | command |
| bot.py:10982 | `member_of_the_week_loop` | scheduled_loop |
| bot.py:11081 | `motw_set_schedule` | command |
| bot.py:11102 | `motw_set_channel` | command |
| bot.py:11129 | `motw_test` | command |
| bot.py:13276 | `CondemnationPardonView` | view_or_modal |
| bot.py:14042 | `moderation_case_expiry_loop` | scheduled_loop |
| bot.py:14077 | `condemnation_expiry_loop` | scheduled_loop |
| bot.py:14191 | `honeypot_listener` | event |
| bot.py:14224 | `honeypot_channel_deleted` | event |
| bot.py:14250 | `condenar` | command |
| bot.py:14306 | `PendingRoleRestoreView` | view_or_modal |
| bot.py:14314 | `PendingRoleRestoreView.interaction_check` | interaction_hook |
| bot.py:14324 | `PendingRoleRestoreView.confirm` | component_callback |
| bot.py:14415 | `PendingRoleRestoreView.cancel` | component_callback |
| bot.py:14433 | `restaurar_roles_pendientes` | command |
| bot.py:14460 | `liberar` | command |
| bot.py:14478 | `condenar_config` | command |
| bot.py:14501 | `ConfigurationConfirmView` | view_or_modal |
| bot.py:14510 | `ConfigurationConfirmView.interaction_check` | interaction_hook |
| bot.py:14514 | `ConfigurationConfirmView.save` | component_callback |
| bot.py:14658 | `ConfigurationConfirmView.cancel` | component_callback |
| bot.py:14693 | `CondemnationCoreModal` | view_or_modal |
| bot.py:14721 | `CondemnationCoreModal.on_submit` | interaction_hook |
| bot.py:14740 | `CondemnationDetailsModal` | view_or_modal |
| bot.py:14757 | `CondemnationDetailsModal.on_submit` | interaction_hook |
| bot.py:14768 | `CondemnationDurationModal` | view_or_modal |
| bot.py:14783 | `CondemnationDurationModal.on_submit` | interaction_hook |
| bot.py:14796 | `CondemnationMoreDetailsModal` | view_or_modal |
| bot.py:14813 | `CondemnationMoreDetailsModal.on_submit` | interaction_hook |
| bot.py:14824 | `CondemnationButtonUrlModal` | view_or_modal |
| bot.py:14838 | `CondemnationButtonUrlModal.on_submit` | interaction_hook |
| bot.py:14928 | `CondemnationTemplateEditorView` | view_or_modal |
| bot.py:14934 | `CondemnationTemplateEditorView.interaction_check` | interaction_hook |
| bot.py:14946 | `CondemnationTemplateEditorView.edit_core` | component_callback |
| bot.py:14950 | `CondemnationTemplateEditorView.edit_details` | component_callback |
| bot.py:14954 | `CondemnationTemplateEditorView.edit_more_details` | component_callback |
| bot.py:14958 | `CondemnationTemplateEditorView.edit_button_url` | component_callback |
| bot.py:14962 | `CondemnationTemplateEditorView.edit_duration` | component_callback |
| bot.py:14966 | `CondemnationTemplateEditorView.preview` | component_callback |
| bot.py:14977 | `CondemnationTemplateEditorView.reset` | component_callback |
| bot.py:14983 | `CondemnationTemplateEditorView.back_to_heraldo` | component_callback |
| bot.py:15007 | `condenar_template` | command |
| bot.py:15028 | `moderation_reaction_add` | event |
| bot.py:15187 | `ReactionCondemnReasonModal` | view_or_modal |
| bot.py:15201 | `ReactionCondemnReasonModal.on_submit` | interaction_hook |
| bot.py:15270 | `ReactionCondemnReasonView` | view_or_modal |
| bot.py:15284 | `ReactionCondemnReasonView.interaction_check` | interaction_hook |
| bot.py:15291 | `ReactionCondemnReasonView.enter_reason` | component_callback |
| bot.py:15295 | `ReactionCondemnReasonView.cancel` | component_callback |
| bot.py:15300 | `ReactionCondemnReasonView.on_timeout` | interaction_hook |
| bot.py:15317 | `HoneypotGroup.interaction_check` | interaction_hook |
| bot.py:15332 | `HoneypotWarningModal` | view_or_modal |
| bot.py:15346 | `HoneypotWarningModal.on_submit` | interaction_hook |
| bot.py:15370 | `honeypot_config` | command |
| bot.py:15446 | `HoneypotTrapActionConfirmView` | view_or_modal |
| bot.py:15454 | `HoneypotTrapActionConfirmView.interaction_check` | interaction_hook |
| bot.py:15458 | `HoneypotTrapActionConfirmView.confirm` | component_callback |
| bot.py:15551 | `HoneypotTrapActionConfirmView.cancel` | component_callback |
| bot.py:15566 | `honeypot_add` | command |
| bot.py:15587 | `honeypot_create` | command |
| bot.py:15605 | `honeypot_remove` | command |
| bot.py:15617 | `HoneypotWarningEmbedModal` | view_or_modal |
| bot.py:15655 | `HoneypotWarningEmbedModal.on_submit` | interaction_hook |
| bot.py:15685 | `honeypot_warning_embed_cmd` | command |
| bot.py:15690 | `honeypot_warning_text_cmd` | command |
| bot.py:15694 | `HoneypotExemptionConfirmView` | view_or_modal |
| bot.py:15701 | `HoneypotExemptionConfirmView.interaction_check` | interaction_hook |
| bot.py:15705 | `HoneypotExemptionConfirmView.confirm` | component_callback |
| bot.py:15731 | `HoneypotExemptionConfirmView.cancel` | component_callback |
| bot.py:15746 | `honeypot_exempt_add` | command |
| bot.py:15772 | `honeypot_exempt_remove` | command |
| bot.py:15798 | `honeypot_history` | command |
| bot.py:15826 | `honeypot_resume` | command |
| bot.py:15873 | `FusionChannelsView` | view_or_modal |
| bot.py:15891 | `FusionChannelsView.interaction_check` | interaction_hook |
| bot.py:15900 | `FusionChannelsView.confirm` | component_callback |
| bot.py:15920 | `FusionChannelsView.cancel` | component_callback |
| bot.py:16250 | `fusionar_canales` | command |
| bot.py:16370 | `PurgeConfirmView` | view_or_modal |
| bot.py:16376 | `PurgeConfirmView.interaction_check` | interaction_hook |
| bot.py:16380 | `PurgeConfirmView.confirm` | component_callback |
| bot.py:16386 | `PurgeConfirmView.cancel` | component_callback |
| bot.py:16396 | `moderation_warn` | command |
| bot.py:16413 | `moderation_mute` | command |
| bot.py:16428 | `moderation_kick` | command |
| bot.py:16438 | `moderation_ban` | command |
| bot.py:16454 | `moderation_caseinfo` | command |
| bot.py:16471 | `moderation_caselist` | command |
| bot.py:16488 | `moderation_caseupdate` | command |
| bot.py:16516 | `moderation_setproof` | command |
| bot.py:16535 | `moderation_caseclose` | command |
| bot.py:16557 | `moderation_casedelete` | command |
| bot.py:16587 | `purge_command` | command |
| bot.py:17091 | `raid_expiry_loop` | scheduled_loop |
| bot.py:17154 | `raid_config` | command |
| bot.py:17235 | `raid_status` | command |
| bot.py:17246 | `raid_start_command` | command |
| bot.py:17261 | `raid_end_command` | command |
| bot.py:17548 | `variables_command` | command |
| bot.py:17659 | `list_commands_command` | command |
| bot.py:17673 | `list_variables_command` | command |
| bot.py:17680 | `list_condemned_command` | command |
| bot.py:17726 | `list_embeds_command` | command |
| bot.py:18199 | `EmbedContentModal` | view_or_modal |
| bot.py:18222 | `EmbedContentModal.on_submit` | interaction_hook |
| bot.py:18245 | `EmbedAuthorFooterModal` | view_or_modal |
| bot.py:18269 | `EmbedAuthorFooterModal.on_submit` | interaction_hook |
| bot.py:18287 | `EmbedFieldModal` | view_or_modal |
| bot.py:18300 | `EmbedFieldModal.on_submit` | interaction_hook |
| bot.py:18316 | `EmbedChannelPicker` | view_or_modal |
| bot.py:18330 | `EmbedChannelPicker.interaction_check` | interaction_hook |
| bot.py:18347 | `EmbedEditorView` | view_or_modal |
| bot.py:18365 | `EmbedEditorView.interaction_check` | interaction_hook |
| bot.py:18379 | `EmbedEditorView.edit_content` | component_callback |
| bot.py:18386 | `EmbedEditorView.edit_author` | component_callback |
| bot.py:18393 | `EmbedEditorView.add_field` | component_callback |
| bot.py:18397 | `EmbedEditorView.toggle_time` | component_callback |
| bot.py:18424 | `EmbedEditorView.save_changes` | component_callback |
| bot.py:18442 | `EmbedEditorView.discard_changes` | component_callback |
| bot.py:18448 | `EmbedEditorView.send_embed` | component_callback |
| bot.py:18508 | `embed_create` | command |
| bot.py:18522 | `embed_edit` | command |
| bot.py:18536 | `embed_send_command` | command |
| bot.py:18548 | `embed_delete_command` | command |
| bot.py:18794 | `SuggestionPanelView` | view_or_modal |
| bot.py:18815 | `SuggestionModal` | view_or_modal |
| bot.py:18830 | `SuggestionModal.on_submit` | interaction_hook |
| bot.py:18905 | `SuggestionRejectModal` | view_or_modal |
| bot.py:18919 | `SuggestionRejectModal.on_submit` | interaction_hook |
| bot.py:18928 | `SuggestionReviewView` | view_or_modal |
| bot.py:19145 | `SuggestionPanelConfirmView` | view_or_modal |
| bot.py:19153 | `SuggestionPanelConfirmView.interaction_check` | interaction_hook |
| bot.py:19157 | `SuggestionPanelConfirmView.confirm` | component_callback |
| bot.py:19195 | `SuggestionPanelConfirmView.cancel` | component_callback |
| bot.py:19211 | `suggestions_panel` | command |
| bot.py:19230 | `SuggestionSettingsConfirmView` | view_or_modal |
| bot.py:19241 | `SuggestionSettingsConfirmView.interaction_check` | interaction_hook |
| bot.py:19245 | `SuggestionSettingsConfirmView.confirm` | component_callback |
| bot.py:19282 | `SuggestionSettingsConfirmView.cancel` | component_callback |
| bot.py:19296 | `suggestions_config` | command |
| bot.py:19310 | `suggestions_reviewer_add` | command |
| bot.py:19326 | `suggestions_reviewer_remove` | command |
| bot.py:19341 | `suggestions_list` | command |
| bot.py:19374 | `SuggestionPanelEditorModal` | view_or_modal |
| bot.py:19409 | `SuggestionPanelEditorModal.on_submit` | interaction_hook |
| bot.py:19428 | `HeraldoMessagesView` | view_or_modal |
| bot.py:19434 | `HeraldoMessagesView.interaction_check` | interaction_hook |
| bot.py:19443 | `HeraldoMessagesView.verification` | component_callback |
| bot.py:19449 | `HeraldoMessagesView.suggestions` | component_callback |
| bot.py:19455 | `HeraldoMessagesView.honeypot` | component_callback |
| bot.py:19461 | `HeraldoMessagesView.verify_dm` | component_callback |
| bot.py:19467 | `HeraldoMessagesView.condemnations` | component_callback |
| bot.py:19473 | `HeraldoMessagesView.logs` | component_callback |
| bot.py:19481 | `HeraldoMessagesView.custom_embeds` | component_callback |
| bot.py:19495 | `HeraldoMessagesView.close` | component_callback |
| bot.py:19506 | `mensajes_command` | command |
| message_automation.py:235 | `ScheduledMessages.worker` | scheduled_loop |
| message_automation.py:254 | `install.create` | command |
| message_automation.py:283 | `install.listing` | command |
| message_automation.py:296 | `install.remove` | command |
| message_automation.py:321 | `install_autoresponses.create` | command |
| message_automation.py:350 | `install_autoresponses.listing` | command |
| message_automation.py:361 | `install_autoresponses.remove` | command |
| message_automation.py:381 | `install_sticky.create` | command |
| message_automation.py:405 | `install_sticky.listing` | command |
| message_automation.py:416 | `install_sticky.remove` | command |
| message_automation.py:430 | `WebhookTemplateConfirmView` | view_or_modal |
| message_automation.py:437 | `WebhookTemplateConfirmView.interaction_check` | interaction_hook |
| message_automation.py:441 | `WebhookTemplateConfirmView.publish` | component_callback |
| message_automation.py:486 | `WebhookTemplateConfirmView.cancel` | component_callback |
| message_automation.py:501 | `install_webhook.publish` | command |
| message_components.py:89 | `ActionConfirm` | view_or_modal |
| message_components.py:96 | `ActionConfirm.interaction_check` | interaction_hook |
| message_components.py:103 | `ActionConfirm.execute` | component_callback |
| message_components.py:205 | `ActionConfirm.cancel` | component_callback |
| message_components.py:218 | `install.dispatch` | event |
| message_components.py:257 | `install.configure` | command |
| message_editor.py:9 | `VisualModal` | view_or_modal |
| message_editor.py:38 | `VisualModal.on_submit` | interaction_hook |
| message_editor.py:107 | `VisualEditor` | view_or_modal |
| message_editor.py:138 | `VisualEditor.interaction_check` | interaction_hook |
| message_editor.py:161 | `VisualEditor.add_embed` | component_callback |
| message_editor.py:171 | `VisualEditor.remove_embed` | component_callback |
| message_editor.py:179 | `VisualEditor.preview` | component_callback |
| message_editor.py:189 | `VisualEditor.save` | component_callback |
| message_editor.py:207 | `VisualEditor.cancel` | component_callback |
| message_editor.py:216 | `install.editor` | command |

## Pruebas disponibles

- `test_member_logs.py:23` — `MemberLogRegressions.test_disabled_by_default_and_separate_per_server`
- `test_member_logs.py:30` — `MemberLogRegressions.test_channel_per_event`
- `test_member_logs.py:36` — `MemberLogRegressions.test_event_category`
- `test_member_logs.py:41` — `MemberLogRegressions.test_editor_draft_does_not_save_immediately`
- `test_regressions.py:57` — `Regressions.test_message_template_requires_explicit_save`
- `test_regressions.py:71` — `Regressions.test_message_confirmation_cancel_keeps_configuration`
- `test_regressions.py:81` — `Regressions.test_message_kit_conflict_does_not_overwrite_existing`
- `test_regressions.py:92` — `Regressions.test_message_confirm_rejects_other_admin_session`
- `test_regressions.py:102` — `Regressions.test_preference_verification_logs_its_own_event`
- `test_regressions.py:114` — `Regressions.test_member_logs_disabled_until_admin_confirms`
- `test_regressions.py:123` — `Regressions.test_member_logs_event_isolation`
- `test_regressions.py:133` — `Regressions.test_log_template_draft_requires_confirmation`
- `test_regressions.py:149` — `Regressions.test_member_log_confirmation_requires_admin`
- `test_regressions.py:158` — `Regressions.test_log_template_reset_is_explicit`
- `test_regressions.py:172` — `Regressions.test_raid_setup_read_and_write`
- `test_regressions.py:184` — `Regressions.test_startup_layouts_and_serialization`
- `test_regressions.py:199` — `Regressions.test_editor_state_isolation`
- `test_regressions.py:207` — `Regressions.test_database_restart_and_guild_isolation`
- `test_regressions.py:218` — `Regressions.test_command_registration_payloads`
- `test_regressions.py:231` — `Regressions.test_save_keeps_active_reaction`
- `test_regressions.py:240` — `Regressions.test_create_role_for_active_reaction_and_cache_delay`
- `test_regressions.py:268` — `Regressions.test_create_role_guards`
- `test_regressions.py:287` — `Regressions.test_create_role_discord_error_preserves_draft`
- `test_regressions.py:300` — `Regressions.test_creation_menu_opens_modal_for_selected_reaction`
- `test_regressions.py:309` — `Regressions.test_modal_updates_original_message`
- `test_regressions.py:325` — `Regressions.test_conflicting_role_actions_rejected`
- `test_regressions.py:335` — `Regressions.test_deleted_message_can_be_unregistered`
- `test_regressions.py:347` — `Regressions.test_rejected_reaction_removal_does_not_change_roles`
- `test_regressions.py:356` — `Regressions.test_maximum_rejects_then_ignores_automatic_removal`
- `test_regressions.py:369` — `Regressions.test_failed_rejection_does_not_ignore_future_removal`
- `test_regressions.py:376` — `Regressions.test_reaction_add_remove_and_reverse`
- `test_regressions.py:404` — `Regressions.test_join_inline_creation_preserves_draft_and_cache_miss`
- `test_regressions.py:431` — `Regressions.test_join_creation_denied_does_not_create`
- `test_regressions.py:439` — `Regressions.test_join_discard_resets_visual_and_user_draft`
- `test_regressions.py:453` — `Regressions.test_reports_summary_uses_draft_and_discard_resets_channel`
- `test_regressions.py:465` — `Regressions.test_rr_events_are_serial_and_locks_cleaned`
- `test_regressions.py:482` — `Regressions.test_join_delay_is_draft_until_save`
- `test_regressions.py:494` — `Regressions.test_join_creation_limit_and_http_failure_preserve_draft`
- `test_regressions.py:511` — `Regressions.test_simultaneous_reactions_keep_one_under_limit`
- `tests/test_evidence_access_regressions.py:15` — `EvidenceAndRoleSafetyTests.test_evidence_archive_rejects_non_admin_role_access`
- `tests/test_evidence_access_regressions.py:23` — `EvidenceAndRoleSafetyTests.test_evidence_archive_rejects_member_overrides`
- `tests/test_evidence_access_regressions.py:30` — `EvidenceAndRoleSafetyTests.test_partial_restoration_keeps_role_identifiers_for_private_log`
- `tests/test_evidence_access_regressions.py:60` — `EvidenceRuntimeTests.test_ordinary_role_access_blocks_copy_before_send`
- `tests/test_evidence_access_regressions.py:68` — `EvidenceRuntimeTests.test_member_override_blocks_copy_before_send`
- `tests/test_evidence_access_regressions.py:76` — `EvidenceRuntimeTests.test_incomplete_attachment_copy_never_authorizes_purge`
- `tests/test_evidence_access_regressions.py:85` — `EvidenceRuntimeTests.test_complete_private_copy_returns_archive_reference`
- `tests/test_log_category_select_regression.py:8` — `LogCategorySelectTests.test_log_category_options_do_not_use_invalid_emoji`
- `tests/test_message_automation.py:37` — `SchedulingTests.test_local_time_and_invalid_dst`
- `tests/test_message_automation.py:43` — `SchedulingTests.test_daily_recurrence_preserves_local_hour_across_dst`
- `tests/test_message_automation.py:48` — `SchedulingTests.test_one_off_is_not_repeated`
- `tests/test_message_automation.py:55` — `SchedulingTests.test_permission_revocation_blocks_send`
- `tests/test_message_automation.py:61` — `SchedulingTests.test_timeout_does_not_blindly_repeat`
- `tests/test_message_automation.py:68` — `SchedulingTests.test_restart_preserves_pending_but_flags_inflight`
- `tests/test_message_automation.py:78` — `SchedulingTests.test_claim_is_scoped_to_guild`
- `tests/test_message_automation.py:95` — `AutoresponseTests.test_keyword_has_boundaries_and_is_not_regular_expression`
- `tests/test_message_automation.py:101` — `AutoresponseTests.test_response_context_and_persistent_cooldown`
- `tests/test_message_automation.py:110` — `AutoresponseTests.test_channel_limit_covers_different_rules`
- `tests/test_message_automation.py:117` — `AutoresponseTests.test_bots_webhooks_and_condemnations_do_not_trigger`
- `tests/test_message_automation.py:140` — `StickyTests.test_sticky_waits_for_activity_and_deletes_only_previous_bot_message`
- `tests/test_message_automation.py:152` — `StickyTests.test_sticky_never_deletes_someone_elses_message`
- `tests/test_message_automation.py:161` — `StickyTests.test_message_during_send_is_not_lost`
- `tests/test_message_automation.py:169` — `StickyTests.test_other_channel_does_not_trigger`
- `tests/test_message_automation.py:194` — `WebhookTests.test_cancel_never_contacts_webhooks`
- `tests/test_message_automation.py:199` — `WebhookTests.test_confirm_reuses_only_owned_webhook_once`
- `tests/test_message_automation.py:205` — `WebhookTests.test_foreign_webhook_is_never_used`
- `tests/test_message_automation.py:213` — `WebhookTests.test_revoked_channel_permission_blocks_creation`
- `tests/test_message_automation.py:219` — `WebhookTests.test_changed_template_requires_new_confirmation`
- `tests/test_message_editors.py:25` — `EditorTests.test_visual_changes_remain_draft_until_confirmation`
- `tests/test_message_editors.py:35` — `EditorTests.test_visual_concurrent_changes_are_not_overwritten`
- `tests/test_message_editors.py:41` — `EditorTests.test_stale_visual_modal_is_rejected`
- `tests/test_message_editors.py:49` — `EditorTests.test_empty_embed_cannot_be_saved`
- `tests/test_message_editors.py:55` — `EditorTests.test_components_independent_options_and_multiple_selection`
- `tests/test_message_editors.py:67` — `EditorTests.test_components_reject_limits_and_invalid_types`
- `tests/test_message_editors.py:75` — `EditorTests.test_component_cancel_has_no_effects`
- `tests/test_message_editors.py:81` — `EditorTests.test_component_other_owner_is_rejected`
- `tests/test_message_editors.py:85` — `EditorTests.test_visual_long_description_is_not_silently_truncated`
- `tests/test_message_editors.py:91` — `EditorTests.test_modal_from_closed_editor_cannot_reopen_draft`
- `tests/test_message_editors.py:100` — `EditorTests.test_component_partial_failure_stops_sequence_and_persists_audit`
- `tests/test_message_editors.py:126` — `EditorTests.test_component_revoked_author_and_active_condemnation_block_actions`
- `tests/test_message_payload.py:9` — `MessagePayloadTests.test_plain_content_and_variables`
- `tests/test_message_payload.py:14` — `MessagePayloadTests.test_legacy_embed_still_renders`
- `tests/test_message_payload.py:19` — `MessagePayloadTests.test_rich_multi_embed`
- `tests/test_message_payload.py:26` — `MessagePayloadTests.test_limits_and_types`
- `tests/test_message_payload.py:36` — `MessagePayloadTests.test_variable_expansion_is_revalidated`
- `tests/test_message_payload.py:40` — `MessagePayloadTests.test_kit_strips_actions_and_preserves_visuals`
- `tests/test_message_payload.py:47` — `MessagePayloadTests.test_kit_duplicate_names_rejected`
- `tests/test_reaction_reports_ux.py:10` — `ReactionReportUxTests.test_all_visible_setup_sections_open_and_serialize`
- `tests/test_reaction_reports_ux.py:26` — `ReactionReportUxTests.test_report_ledger_survives_connection_changes_and_isolates_guilds`
- `tests/test_reaction_reports_ux.py:35` — `ReactionReportUxTests.test_rule_default_labels_round_trip_for_every_action`
- `tests/test_reaction_reports_ux.py:50` — `ReactionReportUxTests.test_rule_modal_revoked_permission_cannot_mutate_draft`
- `tests/test_reaction_reports_ux.py:60` — `ReactionReportUxTests.test_setup_selection_executes_real_navigation_callback`
- `tests/test_reaction_reports_ux.py:68` — `ReactionReportUxTests.test_report_condemn_delegates_purge_to_evidence_safe_path`
- `tests/test_reaction_reports_ux.py:85` — `ReactionReportUxTests.test_failed_report_condemn_never_purges`
- `tests/test_reaction_reports_ux.py:100` — `ReactionReportUxTests.test_reaction_resolves_member_and_posts_single_result`
- `tests/test_reaction_reports_ux.py:143` — `ReactionReportUxTests.test_setup_navigates_on_selection_without_extra_button`
- `tests/test_safety_regressions.py:31` — `SafetyTests.test_condemnation_snapshot_exists_before_remote_role_edit`
- `tests/test_safety_regressions.py:44` — `SafetyTests.test_honeypot_warning_requires_confirmation_and_cancel_preserves_value`
- `tests/test_safety_regressions.py:57` — `SafetyTests.test_honeypot_embed_revoked_permission_never_proposes_change`
- `tests/test_safety_regressions.py:68` — `SafetyTests.test_explicit_template_bypasses_global_embed_conversion`
- `tests/test_safety_regressions.py:76` — `SafetyTests.test_template_limit_not_increased_by_automatic_footer`
- `tests/test_safety_regressions.py:84` — `SafetyTests.test_setup_times_are_only_saved_after_confirmation`
- `tests/test_safety_regressions.py:97` — `SafetyTests.test_setup_modal_with_revoked_permission_never_saves`
- `tests/test_safety_regressions.py:106` — `SafetyTests.test_join_queue_survives_new_connection_and_does_not_reset_delay`
- `tests/test_safety_regressions.py:118` — `SafetyTests.test_join_queue_recovers_without_repeating_delay`
- `tests/test_safety_regressions.py:133` — `SafetyTests.test_join_queue_preserves_unavailable_server`
- `tests/test_safety_regressions.py:143` — `SafetyTests.test_departure_without_audit_does_not_claim_voluntary_exit`
- `tests/test_safety_regressions.py:149` — `SafetyTests.test_departure_retries_delayed_audit`
- `tests/test_safety_regressions.py:162` — `SafetyTests.test_evidence_rejects_other_authors_before_fallback`
- `tests/test_safety_regressions.py:168` — `SafetyTests.test_self_service_denies_administrative_roles`
- `tests/test_safety_regressions.py:173` — `SafetyTests.test_condemned_member_cannot_use_role_component`
- `tests/test_safety_regressions.py:198` — `SafetyTests.test_new_condemnation_persists_configured_role`
- `tests/test_safety_regressions.py:212` — `SafetyTests.test_same_member_different_guild_does_not_block`
- `tests/test_safety_regressions.py:222` — `SafetyTests.test_release_during_condemnation_is_rejected`
- `tests/test_safety_regressions.py:230` — `SafetyTests.test_release_lock_is_cleaned_after_failure`
- `tests/test_safety_regressions.py:237` — `SafetyTests.test_configuration_cancel_and_save`
- `tests/test_safety_regressions.py:246` — `SafetyTests.test_configuration_rejects_stale_draft`
- `tests/test_safety_regressions.py:253` — `SafetyTests.test_lost_permission_blocks_confirm_and_join_panel`
- `tests/test_safety_regressions.py:259` — `SafetyTests.test_other_guild_blocked`
- `tests/test_safety_regressions.py:263` — `SafetyTests.test_condemnation_design_modal_only_proposes`
- `tests/test_safety_regressions.py:272` — `SafetyTests.test_channel_selector_has_no_invalid_emoji`
- `tests/test_safety_regressions.py:278` — `SafetyTests.test_expiry_fetches_member_when_cache_misses`
- `tests/test_safety_regressions.py:290` — `SafetyTests.test_expiry_preserves_case_when_guild_unavailable`
- `tests/test_safety_regressions.py:298` — `SafetyTests.test_honeypot_setup_cancel_does_not_save`
- `tests/test_safety_regressions.py:309` — `SafetyTests.test_honeypot_resume_uses_confirmed_save`
- `tests/test_safety_regressions.py:319` — `SafetyTests.test_log_channel_change_waits_for_confirmation`
- `tests/test_safety_regressions.py:334` — `SafetyTests.test_verify_setup_cancel_preserves_previous_settings`
- `tests/test_safety_regressions.py:343` — `SafetyTests.test_joinroles_add_cancel_preserves_existing_roles`
- `tests/test_safety_regressions.py:354` — `SafetyTests.test_motw_schedule_cancel_preserves_values`
- `tests/test_safety_regressions.py:365` — `SafetyTests.test_honeypot_add_cancel_keeps_channel_unregistered`
- `tests/test_safety_regressions.py:380` — `SafetyTests.test_honeypot_remove_cancel_keeps_channel_registered`
- `tests/test_safety_regressions.py:391` — `SafetyTests.test_honeypot_create_cancel_creates_no_channel`
- `tests/test_safety_regressions.py:404` — `SafetyTests.test_honeypot_exemption_cancel_has_no_database_write`
- `tests/test_safety_regressions.py:416` — `SafetyTests.test_raid_setup_cancel_keeps_threshold`
- `tests/test_safety_regressions.py:426` — `SafetyTests.test_suggestion_owner_cancel_keeps_current_state`
- `tests/test_safety_regressions.py:436` — `SafetyTests.test_suggestion_reviewer_cancel_keeps_list`
- `tests/test_safety_regressions.py:446` — `SafetyTests.test_suggestion_panel_cancel_does_not_publish`
- `tests/test_safety_regressions.py:462` — `SafetyTests.test_condemnation_channel_cancel_preserves_setting`
- `tests/test_safety_regressions.py:476` — `SafetyTests.test_pending_roles_are_scoped_and_persist_after_case_closed`
- `tests/test_safety_regressions.py:483` — `SafetyTests.test_pending_restore_cancel_never_assigns_roles`
- `tests/test_safety_regressions.py:491` — `SafetyTests.test_pending_restore_confirm_assigns_and_clears_pending`
- `tests/test_safety_regressions.py:509` — `SafetyTests.test_pending_restore_denies_revoked_permissions`
- `tests/test_safety_regressions.py:515` — `SafetyTests.test_pending_restore_defers_before_fetch_and_preserves_roles_on_api_error`
- `tests/test_safety_regressions.py:536` — `SafetyTests.test_pending_restore_rechecks_roles_permission_after_fetch`
- `tests/test_safety_regressions.py:556` — `SafetyTests.test_pending_restore_cancel_during_fetch_prevents_role_assignment`
