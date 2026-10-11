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
| bot.py:2497 | `check_pending_verifications` | scheduled_loop |
| bot.py:2745 | `HeraldoGeneralConfigModal` | view_or_modal |
| bot.py:2772 | `HeraldoGeneralConfigModal.on_submit` | interaction_hook |
| bot.py:2981 | `HeraldoChannelSetupView` | view_or_modal |
| bot.py:3034 | `HeraldoChannelSetupView.interaction_check` | interaction_hook |
| bot.py:3198 | `HeraldoRoleSetupView` | view_or_modal |
| bot.py:3229 | `HeraldoRoleSetupView.interaction_check` | interaction_hook |
| bot.py:3335 | `HeraldoRoleSetupView.save_changes` | component_callback |
| bot.py:3352 | `HeraldoRoleSetupView.discard_changes` | component_callback |
| bot.py:3360 | `HeraldoRoleSetupView.back` | component_callback |
| bot.py:3364 | `JoinRolesDelayModal` | view_or_modal |
| bot.py:3378 | `JoinRolesDelayModal.on_submit` | interaction_hook |
| bot.py:3395 | `JoinRolesScheduleModal` | view_or_modal |
| bot.py:3408 | `JoinRolesScheduleModal.on_submit` | interaction_hook |
| bot.py:3430 | `_JoinRolesOwnedView` | view_or_modal |
| bot.py:3436 | `_JoinRolesOwnedView.interaction_check` | interaction_hook |
| bot.py:3447 | `HeraldoJoinRolesSetupView` | view_or_modal |
| bot.py:3449 | `HeraldoJoinRolesSetupView.basic` | component_callback |
| bot.py:3457 | `HeraldoJoinRolesSetupView.users` | component_callback |
| bot.py:3465 | `HeraldoJoinRolesSetupView.bots` | component_callback |
| bot.py:3473 | `HeraldoJoinRolesSetupView.synchronization` | component_callback |
| bot.py:3481 | `HeraldoJoinRolesSetupView.back` | component_callback |
| bot.py:3492 | `JoinRolesCreateRoleModal` | view_or_modal |
| bot.py:3499 | `JoinRolesCreateRoleModal.on_submit` | interaction_hook |
| bot.py:3541 | `HeraldoJoinRolesBasicView` | view_or_modal |
| bot.py:3559 | `HeraldoJoinRolesBasicView.create_role` | component_callback |
| bot.py:3595 | `HeraldoJoinRolesBasicView.screening` | component_callback |
| bot.py:3606 | `HeraldoJoinRolesBasicView.delay` | component_callback |
| bot.py:3610 | `HeraldoJoinRolesBasicView.enable` | component_callback |
| bot.py:3624 | `HeraldoJoinRolesBasicView.disable` | component_callback |
| bot.py:3634 | `HeraldoJoinRolesBasicView.save_changes` | component_callback |
| bot.py:3660 | `HeraldoJoinRolesBasicView.discard_changes` | component_callback |
| bot.py:3672 | `HeraldoJoinRolesBasicView.back` | component_callback |
| bot.py:3679 | `JoinRolesUserIdModal` | view_or_modal |
| bot.py:3693 | `JoinRolesUserIdModal.on_submit` | interaction_hook |
| bot.py:3712 | `HeraldoJoinRolesUsersView` | view_or_modal |
| bot.py:3729 | `HeraldoJoinRolesUsersView.create_role` | component_callback |
| bot.py:3749 | `HeraldoJoinRolesUsersView.set_user_id` | component_callback |
| bot.py:3758 | `HeraldoJoinRolesUsersView.save_user` | component_callback |
| bot.py:3775 | `HeraldoJoinRolesUsersView.remove_user` | component_callback |
| bot.py:3787 | `HeraldoJoinRolesUsersView.remove_after` | component_callback |
| bot.py:3793 | `HeraldoJoinRolesUsersView.save_changes` | component_callback |
| bot.py:3802 | `HeraldoJoinRolesUsersView.discard_changes` | component_callback |
| bot.py:3810 | `HeraldoJoinRolesUsersView.back` | component_callback |
| bot.py:3817 | `HeraldoJoinRolesBotsView` | view_or_modal |
| bot.py:3835 | `HeraldoJoinRolesBotsView.create_role` | component_callback |
| bot.py:3867 | `HeraldoJoinRolesBotsView.bot_enabled` | component_callback |
| bot.py:3873 | `HeraldoJoinRolesBotsView.bot_delay` | component_callback |
| bot.py:3879 | `HeraldoJoinRolesBotsView.bot_different` | component_callback |
| bot.py:3890 | `HeraldoJoinRolesBotsView.save_changes` | component_callback |
| bot.py:3908 | `HeraldoJoinRolesBotsView.discard_changes` | component_callback |
| bot.py:3914 | `HeraldoJoinRolesBotsView.back` | component_callback |
| bot.py:3922 | `HeraldoJoinRolesSyncView` | view_or_modal |
| bot.py:3947 | `HeraldoJoinRolesSyncView.sync_now` | component_callback |
| bot.py:3959 | `HeraldoJoinRolesSyncView.schedule` | component_callback |
| bot.py:3963 | `HeraldoJoinRolesSyncView.save_changes` | component_callback |
| bot.py:3975 | `HeraldoJoinRolesSyncView.discard_changes` | component_callback |
| bot.py:3980 | `HeraldoJoinRolesSyncView.back` | component_callback |
| bot.py:3987 | `OrientationEmbedModal` | view_or_modal |
| bot.py:4025 | `OrientationEmbedModal.on_submit` | interaction_hook |
| bot.py:4049 | `HeraldoOrientationSetupView` | view_or_modal |
| bot.py:4077 | `HeraldoOrientationSetupView.interaction_check` | interaction_hook |
| bot.py:4148 | `HeraldoOrientationSetupView.activate` | component_callback |
| bot.py:4153 | `HeraldoOrientationSetupView.deactivate` | component_callback |
| bot.py:4158 | `HeraldoOrientationSetupView.edit_card` | component_callback |
| bot.py:4162 | `HeraldoOrientationSetupView.save_changes` | component_callback |
| bot.py:4218 | `HeraldoOrientationSetupView.discard_changes` | component_callback |
| bot.py:4225 | `HeraldoOrientationSetupView.back` | component_callback |
| bot.py:4230 | `orientation_reaction_add` | event |
| bot.py:4284 | `orientation_reaction_remove` | event |
| bot.py:4308 | `orientation_role_deleted` | event |
| bot.py:4340 | `orientation_message_deleted` | event |
| bot.py:4353 | `HeraldoMotwScheduleModal` | view_or_modal |
| bot.py:4371 | `HeraldoMotwScheduleModal.on_submit` | interaction_hook |
| bot.py:4389 | `HeraldoMotwSetupView` | view_or_modal |
| bot.py:4405 | `HeraldoMotwSetupView.interaction_check` | interaction_hook |
| bot.py:4440 | `HeraldoMotwSetupView.schedule` | component_callback |
| bot.py:4444 | `HeraldoMotwSetupView.test` | component_callback |
| bot.py:4453 | `HeraldoMotwSetupView.save_changes` | component_callback |
| bot.py:4462 | `HeraldoMotwSetupView.discard_changes` | component_callback |
| bot.py:4467 | `HeraldoMotwSetupView.back` | component_callback |
| bot.py:4472 | `HeraldoHoneypotSetupView` | view_or_modal |
| bot.py:4489 | `HeraldoHoneypotSetupView.interaction_check` | interaction_hook |
| bot.py:4520 | `HeraldoHoneypotSetupView.create_channel` | component_callback |
| bot.py:4567 | `HeraldoHoneypotSetupView.toggle` | component_callback |
| bot.py:4577 | `HeraldoHoneypotSetupView.edit_warning` | component_callback |
| bot.py:4581 | `HeraldoHoneypotSetupView.edit_text` | component_callback |
| bot.py:4585 | `HeraldoHoneypotSetupView.save_changes` | component_callback |
| bot.py:4603 | `HeraldoHoneypotSetupView.discard_changes` | component_callback |
| bot.py:4609 | `HeraldoHoneypotSetupView.back` | component_callback |
| bot.py:4669 | `HeraldoVerificationSetupView` | view_or_modal |
| bot.py:4707 | `HeraldoVerificationSetupView.interaction_check` | interaction_hook |
| bot.py:4777 | `HeraldoVerificationSetupView.create_verify_channel` | component_callback |
| bot.py:4814 | `HeraldoVerificationSetupView.create_verify_role` | component_callback |
| bot.py:4830 | `HeraldoVerificationSetupView.create_sin_role` | component_callback |
| bot.py:4846 | `HeraldoVerificationSetupView.texts` | component_callback |
| bot.py:4850 | `HeraldoVerificationSetupView.publish` | component_callback |
| bot.py:4892 | `HeraldoVerificationSetupView.toggle` | component_callback |
| bot.py:4903 | `HeraldoVerificationSetupView.save_changes` | component_callback |
| bot.py:4926 | `HeraldoVerificationSetupView.discard_changes` | component_callback |
| bot.py:4931 | `HeraldoVerificationSetupView.back` | component_callback |
| bot.py:4935 | `HeraldoRaidDetectionModal` | view_or_modal |
| bot.py:4977 | `HeraldoRaidDetectionModal.on_submit` | interaction_hook |
| bot.py:5008 | `HeraldoRaidSetupView` | view_or_modal |
| bot.py:5043 | `HeraldoRaidSetupView.interaction_check` | interaction_hook |
| bot.py:5084 | `HeraldoRaidSetupView.detection` | component_callback |
| bot.py:5088 | `HeraldoRaidSetupView.toggle_enabled` | component_callback |
| bot.py:5095 | `HeraldoRaidSetupView.toggle_invites` | component_callback |
| bot.py:5102 | `HeraldoRaidSetupView.toggle_purge` | component_callback |
| bot.py:5109 | `HeraldoRaidSetupView.save_changes` | component_callback |
| bot.py:5128 | `HeraldoRaidSetupView.discard_changes` | component_callback |
| bot.py:5133 | `HeraldoRaidSetupView.back` | component_callback |
| bot.py:5137 | `VerifyDmEditorContentModal` | view_or_modal |
| bot.py:5184 | `VerifyDmEditorContentModal.on_submit` | interaction_hook |
| bot.py:5210 | `VerifyDmEditorVisualModal` | view_or_modal |
| bot.py:5225 | `VerifyDmEditorVisualModal.on_submit` | interaction_hook |
| bot.py:5241 | `VerifyDmMessageSetupView` | view_or_modal |
| bot.py:5247 | `VerifyDmMessageSetupView.interaction_check` | interaction_hook |
| bot.py:5259 | `VerifyDmMessageSetupView.content` | component_callback |
| bot.py:5263 | `VerifyDmMessageSetupView.visual` | component_callback |
| bot.py:5267 | `VerifyDmMessageSetupView.preview` | component_callback |
| bot.py:5278 | `VerifyDmMessageSetupView.back` | component_callback |
| bot.py:5286 | `SuggestionPanelContentModal` | view_or_modal |
| bot.py:5313 | `SuggestionPanelContentModal.on_submit` | interaction_hook |
| bot.py:5333 | `SuggestionPanelVisualModal` | view_or_modal |
| bot.py:5371 | `SuggestionPanelVisualModal.on_submit` | interaction_hook |
| bot.py:5398 | `SuggestionPanelMessageSetupView` | view_or_modal |
| bot.py:5404 | `SuggestionPanelMessageSetupView.interaction_check` | interaction_hook |
| bot.py:5413 | `SuggestionPanelMessageSetupView.content` | component_callback |
| bot.py:5417 | `SuggestionPanelMessageSetupView.design` | component_callback |
| bot.py:5421 | `SuggestionPanelMessageSetupView.sync` | component_callback |
| bot.py:5430 | `SuggestionPanelMessageSetupView.back` | component_callback |
| bot.py:5537 | `DefaultMessageStudioView` | view_or_modal |
| bot.py:5591 | `DefaultMessageStudioView.interaction_check` | interaction_hook |
| bot.py:6086 | `LogTemplateResetConfirmView` | view_or_modal |
| bot.py:6092 | `LogTemplateResetConfirmView.interaction_check` | interaction_hook |
| bot.py:6102 | `LogTemplateResetConfirmView.confirm` | component_callback |
| bot.py:6108 | `LogTemplateResetConfirmView.cancel` | component_callback |
| bot.py:6113 | `LogTemplateSaveConfirmView` | view_or_modal |
| bot.py:6120 | `LogTemplateSaveConfirmView.interaction_check` | interaction_hook |
| bot.py:6130 | `LogTemplateSaveConfirmView.save` | component_callback |
| bot.py:6137 | `LogTemplateSaveConfirmView.cancel` | component_callback |
| bot.py:6142 | `LogTemplateContentModal` | view_or_modal |
| bot.py:6186 | `LogTemplateContentModal.on_submit` | interaction_hook |
| bot.py:6200 | `LogTemplateVisualModal` | view_or_modal |
| bot.py:6244 | `LogTemplateVisualModal.on_submit` | interaction_hook |
| bot.py:6348 | `LogTemplateEditorView` | view_or_modal |
| bot.py:6453 | `LogTemplateEditorView.interaction_check` | interaction_hook |
| bot.py:6587 | `HeraldoMessageConfirmView` | view_or_modal |
| bot.py:6603 | `HeraldoMessageConfirmView.interaction_check` | interaction_hook |
| bot.py:6612 | `HeraldoMessageConfirmView.commit` | component_callback |
| bot.py:6696 | `HeraldoMessageConfirmView.cancel` | component_callback |
| bot.py:6767 | `HeraldoTemplateModal` | view_or_modal |
| bot.py:6786 | `HeraldoTemplateModal.on_submit` | interaction_hook |
| bot.py:6831 | `HeraldoTemplateRawModal` | view_or_modal |
| bot.py:6840 | `HeraldoTemplateRawModal.on_submit` | interaction_hook |
| bot.py:6860 | `HeraldoTemplateSetupView` | view_or_modal |
| bot.py:6881 | `HeraldoTemplateSetupView.interaction_check` | interaction_hook |
| bot.py:6912 | `HeraldoTemplateSetupView.create` | component_callback |
| bot.py:6916 | `HeraldoTemplateSetupView.edit` | component_callback |
| bot.py:6923 | `HeraldoTemplateSetupView.attach` | component_callback |
| bot.py:6930 | `HeraldoTemplateSetupView.publish` | component_callback |
| bot.py:6953 | `HeraldoTemplateSetupView.edit_raw` | component_callback |
| bot.py:6965 | `HeraldoTemplateSetupView.variables` | component_callback |
| bot.py:6969 | `HeraldoTemplateSetupView.preview` | component_callback |
| bot.py:6984 | `HeraldoTemplateSetupView.delete` | component_callback |
| bot.py:6994 | `HeraldoTemplateSetupView.back` | component_callback |
| bot.py:7011 | `HeraldoMessageRoleModal` | view_or_modal |
| bot.py:7020 | `HeraldoMessageRoleModal.on_submit` | interaction_hook |
| bot.py:7047 | `HeraldoMessageComponentsSetupView` | view_or_modal |
| bot.py:7052 | `HeraldoMessageComponentsSetupView.interaction_check` | interaction_hook |
| bot.py:7061 | `HeraldoMessageComponentsSetupView.create` | component_callback |
| bot.py:7065 | `HeraldoMessageComponentsSetupView.list_components` | component_callback |
| bot.py:7071 | `HeraldoMessageComponentsSetupView.back` | component_callback |
| bot.py:7076 | `HeraldoAttachRoleModal` | view_or_modal |
| bot.py:7084 | `HeraldoAttachRoleModal.on_submit` | interaction_hook |
| bot.py:7183 | `heraldo_message_components_dispatch` | event |
| bot.py:7205 | `HeraldoMessageKitImportModal` | view_or_modal |
| bot.py:7212 | `HeraldoMessageKitImportModal.on_submit` | interaction_hook |
| bot.py:7239 | `HeraldoMessageKitsView` | view_or_modal |
| bot.py:7244 | `HeraldoMessageKitsView.interaction_check` | interaction_hook |
| bot.py:7253 | `HeraldoMessageKitsView.export` | component_callback |
| bot.py:7262 | `HeraldoMessageKitsView.import_kit` | component_callback |
| bot.py:7266 | `HeraldoMessageKitsView.back` | component_callback |
| bot.py:7271 | `HeraldoMessagesSetupView` | view_or_modal |
| bot.py:7302 | `HeraldoMessagesSetupView.interaction_check` | interaction_hook |
| bot.py:7415 | `HeraldoMessagesSetupView.back` | component_callback |
| bot.py:7472 | `ModerationReactionEditModal` | view_or_modal |
| bot.py:7485 | `ModerationReactionEditModal.on_submit` | interaction_hook |
| bot.py:7516 | `ModerationReactionRuleModal` | view_or_modal |
| bot.py:7534 | `ModerationReactionRuleModal.on_submit` | interaction_hook |
| bot.py:7593 | `ModerationCondemnEmojiModal` | view_or_modal |
| bot.py:7601 | `ModerationCondemnEmojiModal.on_submit` | interaction_hook |
| bot.py:7622 | `HeraldoUserReportsSetupView` | view_or_modal |
| bot.py:7642 | `HeraldoUserReportsSetupView.interaction_check` | interaction_hook |
| bot.py:7732 | `HeraldoUserReportsSetupView.add_reaction` | component_callback |
| bot.py:7739 | `HeraldoUserReportsSetupView.edit_reaction` | component_callback |
| bot.py:7746 | `HeraldoUserReportsSetupView.edit_rule` | component_callback |
| bot.py:7753 | `HeraldoUserReportsSetupView.delete_reaction` | component_callback |
| bot.py:7765 | `HeraldoUserReportsSetupView.edit_condemn_emoji` | component_callback |
| bot.py:7769 | `HeraldoUserReportsSetupView.save_changes` | component_callback |
| bot.py:7791 | `HeraldoUserReportsSetupView.discard_changes` | component_callback |
| bot.py:7800 | `HeraldoUserReportsSetupView.back` | component_callback |
| bot.py:7806 | `HeraldoCasesSetupView` | view_or_modal |
| bot.py:7812 | `HeraldoCasesSetupView.interaction_check` | interaction_hook |
| bot.py:7821 | `HeraldoCasesSetupView.refresh` | component_callback |
| bot.py:7825 | `HeraldoCasesSetupView.back` | component_callback |
| bot.py:7831 | `HeraldoCondemnationDurationModal` | view_or_modal |
| bot.py:7845 | `HeraldoCondemnationDurationModal.on_submit` | interaction_hook |
| bot.py:7861 | `HeraldoCondemnationSetupView` | view_or_modal |
| bot.py:7888 | `HeraldoCondemnationSetupView.interaction_check` | interaction_hook |
| bot.py:7946 | `HeraldoCondemnationSetupView.duration` | component_callback |
| bot.py:7950 | `HeraldoCondemnationSetupView.create_channel` | component_callback |
| bot.py:7987 | `HeraldoCondemnationSetupView.create_role` | component_callback |
| bot.py:8003 | `HeraldoCondemnationSetupView.save` | component_callback |
| bot.py:8018 | `HeraldoCondemnationSetupView.discard` | component_callback |
| bot.py:8023 | `HeraldoCondemnationSetupView.back` | component_callback |
| bot.py:8030 | `HeraldoModerationSetupView` | view_or_modal |
| bot.py:8036 | `HeraldoModerationSetupView.interaction_check` | interaction_hook |
| bot.py:8045 | `HeraldoModerationSetupView.condemnations` | component_callback |
| bot.py:8051 | `HeraldoModerationSetupView.cases` | component_callback |
| bot.py:8059 | `HeraldoModerationSetupView.user_reports` | component_callback |
| bot.py:8065 | `HeraldoModerationSetupView.back` | component_callback |
| bot.py:8070 | `HeraldoAutomodSetupView` | view_or_modal |
| bot.py:8076 | `HeraldoAutomodSetupView.interaction_check` | interaction_hook |
| bot.py:8085 | `HeraldoAutomodSetupView.honeypot` | component_callback |
| bot.py:8094 | `HeraldoAutomodSetupView.raid_protection` | component_callback |
| bot.py:8103 | `HeraldoAutomodSetupView.back` | component_callback |
| bot.py:8107 | `HeraldoVerificationHubView` | view_or_modal |
| bot.py:8113 | `HeraldoVerificationHubView.interaction_check` | interaction_hook |
| bot.py:8122 | `HeraldoVerificationHubView.age_verification` | component_callback |
| bot.py:8131 | `HeraldoVerificationHubView.preference_verification` | component_callback |
| bot.py:8140 | `HeraldoVerificationHubView.times` | component_callback |
| bot.py:8144 | `HeraldoVerificationHubView.back` | component_callback |
| bot.py:8148 | `HeraldoLoggingSetupView` | view_or_modal |
| bot.py:8164 | `HeraldoLoggingSetupView.interaction_check` | interaction_hook |
| bot.py:8204 | `HeraldoLoggingSetupView.create_channel` | component_callback |
| bot.py:8241 | `HeraldoLoggingSetupView.member_events` | component_callback |
| bot.py:8246 | `HeraldoLoggingSetupView.save` | component_callback |
| bot.py:8260 | `HeraldoLoggingSetupView.discard` | component_callback |
| bot.py:8265 | `HeraldoLoggingSetupView.back` | component_callback |
| bot.py:8282 | `HeraldoMemberLogSetupView` | view_or_modal |
| bot.py:8299 | `HeraldoMemberLogSetupView.interaction_check` | interaction_hook |
| bot.py:8343 | `HeraldoMemberLogSetupView.toggle` | component_callback |
| bot.py:8349 | `HeraldoMemberLogSetupView.save` | component_callback |
| bot.py:8371 | `HeraldoMemberLogSetupView.discard` | component_callback |
| bot.py:8376 | `HeraldoMemberLogSetupView.back` | component_callback |
| bot.py:8446 | `HeraldoReactionEmojiModal` | view_or_modal |
| bot.py:8453 | `HeraldoReactionEmojiModal.on_submit` | interaction_hook |
| bot.py:8479 | `HeraldoReactionOptionsModal` | view_or_modal |
| bot.py:8491 | `HeraldoReactionOptionsModal.on_submit` | interaction_hook |
| bot.py:8511 | `HeraldoReactionMessageModal` | view_or_modal |
| bot.py:8521 | `HeraldoReactionMessageModal.on_submit` | interaction_hook |
| bot.py:8535 | `HeraldoReactionRoleCreateModal` | view_or_modal |
| bot.py:8546 | `HeraldoReactionRoleCreateModal.on_submit` | interaction_hook |
| bot.py:8603 | `HeraldoReactionRolesEditorView` | view_or_modal |
| bot.py:8687 | `HeraldoReactionRolesEditorView.interaction_check` | interaction_hook |
| bot.py:8783 | `HeraldoReactionRolesEditorView.add_emoji` | component_callback |
| bot.py:8787 | `HeraldoReactionRolesEditorView.options` | component_callback |
| bot.py:8791 | `HeraldoReactionRolesEditorView.edit_message` | component_callback |
| bot.py:8798 | `HeraldoReactionRolesEditorView.save` | component_callback |
| bot.py:8865 | `HeraldoReactionRolesEditorView.back` | component_callback |
| bot.py:8870 | `HeraldoReactionExistingModal` | view_or_modal |
| bot.py:8877 | `HeraldoReactionExistingModal.on_submit` | interaction_hook |
| bot.py:8901 | `HeraldoReactionDeleteModal` | view_or_modal |
| bot.py:8908 | `HeraldoReactionDeleteModal.on_submit` | interaction_hook |
| bot.py:8939 | `HeraldoReactionRolesSetupView` | view_or_modal |
| bot.py:8963 | `HeraldoReactionRolesSetupView.interaction_check` | interaction_hook |
| bot.py:8997 | `HeraldoReactionRolesSetupView.create` | component_callback |
| bot.py:9009 | `HeraldoReactionRolesSetupView.existing` | component_callback |
| bot.py:9013 | `HeraldoReactionRolesSetupView.back` | component_callback |
| bot.py:9130 | `general_reaction_role_add` | event |
| bot.py:9135 | `general_reaction_role_remove` | event |
| bot.py:9139 | `HeraldoPendingSetupModuleView` | view_or_modal |
| bot.py:9146 | `HeraldoPendingSetupModuleView.interaction_check` | interaction_hook |
| bot.py:9155 | `HeraldoPendingSetupModuleView.back` | component_callback |
| bot.py:9159 | `HeraldoSetupView` | view_or_modal |
| bot.py:9199 | `HeraldoSetupView.interaction_check` | interaction_hook |
| bot.py:9272 | `HeraldoSetupView.on_error` | interaction_hook |
| bot.py:9296 | `HeraldoSetupView.close` | component_callback |
| bot.py:9306 | `heraldo_importkit` | command |
| bot.py:9340 | `heraldo_sendtemplate` | command |
| bot.py:9377 | `HeraldoEditTemplateConfirmView` | view_or_modal |
| bot.py:9384 | `HeraldoEditTemplateConfirmView.interaction_check` | interaction_hook |
| bot.py:9394 | `HeraldoEditTemplateConfirmView.confirm` | component_callback |
| bot.py:9427 | `HeraldoEditTemplateConfirmView.cancel` | component_callback |
| bot.py:9435 | `heraldo_edittemplate` | command |
| bot.py:9491 | `setup` | command |
| bot.py:9523 | `heraldo_check` | command |
| bot.py:9550 | `heraldo_check_all` | command |
| bot.py:9635 | `HeraldoLogChannelConfirmView` | view_or_modal |
| bot.py:9645 | `HeraldoLogChannelConfirmView.interaction_check` | interaction_hook |
| bot.py:9649 | `HeraldoLogChannelConfirmView.confirm` | component_callback |
| bot.py:9683 | `HeraldoLogChannelConfirmView.cancel` | component_callback |
| bot.py:9698 | `heraldo_log_channel` | command |
| bot.py:9748 | `VerifyView` | view_or_modal |
| bot.py:10027 | `VerifyTextsModal` | view_or_modal |
| bot.py:10054 | `VerifyTextsModal.on_submit` | interaction_hook |
| bot.py:10068 | `verify` | command |
| bot.py:10130 | `verify_dm_texts` | command |
| bot.py:10210 | `verify_dm_preview` | command |
| bot.py:10246 | `verify_texts` | command |
| bot.py:10264 | `verify_config` | command |
| bot.py:10388 | `joinroles_status` | command |
| bot.py:10402 | `joinroles_sync_command` | command |
| bot.py:10416 | `joinroles_add` | command |
| bot.py:10444 | `joinroles_remove` | command |
| bot.py:10464 | `joinroles_user_add` | command |
| bot.py:10495 | `joinroles_user_remove` | command |
| bot.py:10758 | `template_backup_loop` | scheduled_loop |
| bot.py:10808 | `template_config` | command |
| bot.py:10879 | `template_sync` | command |
| bot.py:10918 | `track_activity` | event |
| bot.py:10937 | `moderation_cache_recent_messages` | event |
| bot.py:10959 | `profile` | command |
| bot.py:11031 | `member_of_the_week_loop` | scheduled_loop |
| bot.py:11130 | `motw_set_schedule` | command |
| bot.py:11151 | `motw_set_channel` | command |
| bot.py:11178 | `motw_test` | command |
| bot.py:13325 | `CondemnationPardonView` | view_or_modal |
| bot.py:14091 | `moderation_case_expiry_loop` | scheduled_loop |
| bot.py:14126 | `condemnation_expiry_loop` | scheduled_loop |
| bot.py:14240 | `honeypot_listener` | event |
| bot.py:14273 | `honeypot_channel_deleted` | event |
| bot.py:14299 | `condenar` | command |
| bot.py:14355 | `PendingRoleRestoreView` | view_or_modal |
| bot.py:14363 | `PendingRoleRestoreView.interaction_check` | interaction_hook |
| bot.py:14373 | `PendingRoleRestoreView.confirm` | component_callback |
| bot.py:14464 | `PendingRoleRestoreView.cancel` | component_callback |
| bot.py:14482 | `restaurar_roles_pendientes` | command |
| bot.py:14509 | `liberar` | command |
| bot.py:14527 | `condenar_config` | command |
| bot.py:14550 | `ConfigurationConfirmView` | view_or_modal |
| bot.py:14559 | `ConfigurationConfirmView.interaction_check` | interaction_hook |
| bot.py:14563 | `ConfigurationConfirmView.save` | component_callback |
| bot.py:14707 | `ConfigurationConfirmView.cancel` | component_callback |
| bot.py:14742 | `CondemnationCoreModal` | view_or_modal |
| bot.py:14770 | `CondemnationCoreModal.on_submit` | interaction_hook |
| bot.py:14789 | `CondemnationDetailsModal` | view_or_modal |
| bot.py:14806 | `CondemnationDetailsModal.on_submit` | interaction_hook |
| bot.py:14817 | `CondemnationDurationModal` | view_or_modal |
| bot.py:14832 | `CondemnationDurationModal.on_submit` | interaction_hook |
| bot.py:14845 | `CondemnationMoreDetailsModal` | view_or_modal |
| bot.py:14862 | `CondemnationMoreDetailsModal.on_submit` | interaction_hook |
| bot.py:14873 | `CondemnationButtonUrlModal` | view_or_modal |
| bot.py:14887 | `CondemnationButtonUrlModal.on_submit` | interaction_hook |
| bot.py:14977 | `CondemnationTemplateEditorView` | view_or_modal |
| bot.py:14983 | `CondemnationTemplateEditorView.interaction_check` | interaction_hook |
| bot.py:14995 | `CondemnationTemplateEditorView.edit_core` | component_callback |
| bot.py:14999 | `CondemnationTemplateEditorView.edit_details` | component_callback |
| bot.py:15003 | `CondemnationTemplateEditorView.edit_more_details` | component_callback |
| bot.py:15007 | `CondemnationTemplateEditorView.edit_button_url` | component_callback |
| bot.py:15011 | `CondemnationTemplateEditorView.edit_duration` | component_callback |
| bot.py:15015 | `CondemnationTemplateEditorView.preview` | component_callback |
| bot.py:15026 | `CondemnationTemplateEditorView.reset` | component_callback |
| bot.py:15032 | `CondemnationTemplateEditorView.back_to_heraldo` | component_callback |
| bot.py:15056 | `condenar_template` | command |
| bot.py:15077 | `moderation_reaction_add` | event |
| bot.py:15236 | `ReactionCondemnReasonModal` | view_or_modal |
| bot.py:15250 | `ReactionCondemnReasonModal.on_submit` | interaction_hook |
| bot.py:15319 | `ReactionCondemnReasonView` | view_or_modal |
| bot.py:15333 | `ReactionCondemnReasonView.interaction_check` | interaction_hook |
| bot.py:15340 | `ReactionCondemnReasonView.enter_reason` | component_callback |
| bot.py:15344 | `ReactionCondemnReasonView.cancel` | component_callback |
| bot.py:15349 | `ReactionCondemnReasonView.on_timeout` | interaction_hook |
| bot.py:15366 | `HoneypotGroup.interaction_check` | interaction_hook |
| bot.py:15381 | `HoneypotWarningModal` | view_or_modal |
| bot.py:15395 | `HoneypotWarningModal.on_submit` | interaction_hook |
| bot.py:15419 | `honeypot_config` | command |
| bot.py:15495 | `HoneypotTrapActionConfirmView` | view_or_modal |
| bot.py:15503 | `HoneypotTrapActionConfirmView.interaction_check` | interaction_hook |
| bot.py:15507 | `HoneypotTrapActionConfirmView.confirm` | component_callback |
| bot.py:15600 | `HoneypotTrapActionConfirmView.cancel` | component_callback |
| bot.py:15615 | `honeypot_add` | command |
| bot.py:15636 | `honeypot_create` | command |
| bot.py:15654 | `honeypot_remove` | command |
| bot.py:15666 | `HoneypotWarningEmbedModal` | view_or_modal |
| bot.py:15704 | `HoneypotWarningEmbedModal.on_submit` | interaction_hook |
| bot.py:15734 | `honeypot_warning_embed_cmd` | command |
| bot.py:15739 | `honeypot_warning_text_cmd` | command |
| bot.py:15743 | `HoneypotExemptionConfirmView` | view_or_modal |
| bot.py:15750 | `HoneypotExemptionConfirmView.interaction_check` | interaction_hook |
| bot.py:15754 | `HoneypotExemptionConfirmView.confirm` | component_callback |
| bot.py:15780 | `HoneypotExemptionConfirmView.cancel` | component_callback |
| bot.py:15795 | `honeypot_exempt_add` | command |
| bot.py:15821 | `honeypot_exempt_remove` | command |
| bot.py:15847 | `honeypot_history` | command |
| bot.py:15875 | `honeypot_resume` | command |
| bot.py:15922 | `FusionChannelsView` | view_or_modal |
| bot.py:15940 | `FusionChannelsView.interaction_check` | interaction_hook |
| bot.py:15949 | `FusionChannelsView.confirm` | component_callback |
| bot.py:15969 | `FusionChannelsView.cancel` | component_callback |
| bot.py:16299 | `fusionar_canales` | command |
| bot.py:16419 | `PurgeConfirmView` | view_or_modal |
| bot.py:16425 | `PurgeConfirmView.interaction_check` | interaction_hook |
| bot.py:16429 | `PurgeConfirmView.confirm` | component_callback |
| bot.py:16435 | `PurgeConfirmView.cancel` | component_callback |
| bot.py:16445 | `moderation_warn` | command |
| bot.py:16462 | `moderation_mute` | command |
| bot.py:16477 | `moderation_kick` | command |
| bot.py:16487 | `moderation_ban` | command |
| bot.py:16503 | `moderation_caseinfo` | command |
| bot.py:16520 | `moderation_caselist` | command |
| bot.py:16537 | `moderation_caseupdate` | command |
| bot.py:16565 | `moderation_setproof` | command |
| bot.py:16584 | `moderation_caseclose` | command |
| bot.py:16606 | `moderation_casedelete` | command |
| bot.py:16636 | `purge_command` | command |
| bot.py:17140 | `raid_expiry_loop` | scheduled_loop |
| bot.py:17203 | `raid_config` | command |
| bot.py:17284 | `raid_status` | command |
| bot.py:17295 | `raid_start_command` | command |
| bot.py:17310 | `raid_end_command` | command |
| bot.py:17597 | `variables_command` | command |
| bot.py:17708 | `list_commands_command` | command |
| bot.py:17722 | `list_variables_command` | command |
| bot.py:17729 | `list_condemned_command` | command |
| bot.py:17775 | `list_embeds_command` | command |
| bot.py:18248 | `EmbedContentModal` | view_or_modal |
| bot.py:18271 | `EmbedContentModal.on_submit` | interaction_hook |
| bot.py:18294 | `EmbedAuthorFooterModal` | view_or_modal |
| bot.py:18318 | `EmbedAuthorFooterModal.on_submit` | interaction_hook |
| bot.py:18336 | `EmbedFieldModal` | view_or_modal |
| bot.py:18349 | `EmbedFieldModal.on_submit` | interaction_hook |
| bot.py:18365 | `EmbedChannelPicker` | view_or_modal |
| bot.py:18379 | `EmbedChannelPicker.interaction_check` | interaction_hook |
| bot.py:18396 | `EmbedEditorView` | view_or_modal |
| bot.py:18414 | `EmbedEditorView.interaction_check` | interaction_hook |
| bot.py:18428 | `EmbedEditorView.edit_content` | component_callback |
| bot.py:18435 | `EmbedEditorView.edit_author` | component_callback |
| bot.py:18442 | `EmbedEditorView.add_field` | component_callback |
| bot.py:18446 | `EmbedEditorView.toggle_time` | component_callback |
| bot.py:18473 | `EmbedEditorView.save_changes` | component_callback |
| bot.py:18491 | `EmbedEditorView.discard_changes` | component_callback |
| bot.py:18497 | `EmbedEditorView.send_embed` | component_callback |
| bot.py:18557 | `embed_create` | command |
| bot.py:18571 | `embed_edit` | command |
| bot.py:18585 | `embed_send_command` | command |
| bot.py:18597 | `embed_delete_command` | command |
| bot.py:18843 | `SuggestionPanelView` | view_or_modal |
| bot.py:18864 | `SuggestionModal` | view_or_modal |
| bot.py:18879 | `SuggestionModal.on_submit` | interaction_hook |
| bot.py:18954 | `SuggestionRejectModal` | view_or_modal |
| bot.py:18968 | `SuggestionRejectModal.on_submit` | interaction_hook |
| bot.py:18977 | `SuggestionReviewView` | view_or_modal |
| bot.py:19194 | `SuggestionPanelConfirmView` | view_or_modal |
| bot.py:19202 | `SuggestionPanelConfirmView.interaction_check` | interaction_hook |
| bot.py:19206 | `SuggestionPanelConfirmView.confirm` | component_callback |
| bot.py:19244 | `SuggestionPanelConfirmView.cancel` | component_callback |
| bot.py:19260 | `suggestions_panel` | command |
| bot.py:19279 | `SuggestionSettingsConfirmView` | view_or_modal |
| bot.py:19290 | `SuggestionSettingsConfirmView.interaction_check` | interaction_hook |
| bot.py:19294 | `SuggestionSettingsConfirmView.confirm` | component_callback |
| bot.py:19331 | `SuggestionSettingsConfirmView.cancel` | component_callback |
| bot.py:19345 | `suggestions_config` | command |
| bot.py:19359 | `suggestions_reviewer_add` | command |
| bot.py:19375 | `suggestions_reviewer_remove` | command |
| bot.py:19390 | `suggestions_list` | command |
| bot.py:19423 | `SuggestionPanelEditorModal` | view_or_modal |
| bot.py:19458 | `SuggestionPanelEditorModal.on_submit` | interaction_hook |
| bot.py:19477 | `HeraldoMessagesView` | view_or_modal |
| bot.py:19483 | `HeraldoMessagesView.interaction_check` | interaction_hook |
| bot.py:19492 | `HeraldoMessagesView.verification` | component_callback |
| bot.py:19498 | `HeraldoMessagesView.suggestions` | component_callback |
| bot.py:19504 | `HeraldoMessagesView.honeypot` | component_callback |
| bot.py:19510 | `HeraldoMessagesView.verify_dm` | component_callback |
| bot.py:19516 | `HeraldoMessagesView.condemnations` | component_callback |
| bot.py:19522 | `HeraldoMessagesView.logs` | component_callback |
| bot.py:19530 | `HeraldoMessagesView.custom_embeds` | component_callback |
| bot.py:19544 | `HeraldoMessagesView.close` | component_callback |
| bot.py:19555 | `mensajes_command` | command |
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
- `tests/test_verification_expiry.py:36` — `VerificationExpiryTests.test_primary_then_role_fallback_expels_and_logs_once`
- `tests/test_verification_expiry.py:43` — `VerificationExpiryTests.test_role_fallback_respects_configured_ban`
- `tests/test_verification_expiry.py:52` — `VerificationExpiryTests.test_role_fallback_respects_log_only_action`
- `tests/test_verification_expiry.py:61` — `VerificationExpiryTests.test_role_fallback_does_not_shorten_extended_primary_deadline`
- `tests/test_verification_expiry.py:67` — `VerificationExpiryTests.test_stale_role_timer_cannot_expire_a_new_role_mark`
- `tests/test_verification_expiry.py:73` — `VerificationExpiryTests.test_standalone_role_fallback_still_expels_once`
- `tests/test_verification_expiry.py:81` — `VerificationExpiryTests.test_verified_member_is_not_expired_by_either_timer`
- `tests/test_verification_expiry.py:89` — `VerificationExpiryTests.test_concurrent_timers_share_one_remote_action`
- `tests/test_verification_expiry.py:105` — `VerificationExpiryTests.test_http_failure_preserves_pending_for_retry`
- `tests/test_verification_expiry.py:117` — `VerificationExpiryTests.test_standalone_fallback_failure_preserves_role_pending`
- `tests/test_verification_expiry.py:125` — `VerificationExpiryTests.test_same_member_in_other_guild_is_not_blocked`
