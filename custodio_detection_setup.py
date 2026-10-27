"""Detección: interpretar, revisar y corregir; Guardar es la única persistencia."""
from __future__ import annotations
from collections import Counter
from dataclasses import replace
import json
import os
import discord
from heraldo_i18n import text as _t, guild_context as _i18n_context
from custodio_interpretation import KEY as PLAN_KEY, InterpretationPlan
from custodio_policy import KEY, ObservePolicy
from custodio_taxonomy import BEHAVIORS
from custodio_detection import KIND_KEYS
from custodio_rule_analysis import analyze as analyze_snapshot
from custodio_source import load_server_rules

STATUS_KEYS = {
    'watchable':'text.custodio.analysis.watchable', 'partial':'text.custodio.analysis.partial',
    'clarification':'text.custodio.analysis.clarification', 'unsupported':'text.custodio.analysis.unsupported',
    'no_prohibition':'text.custodio.analysis.no_prohibition', 'contradiction':'text.custodio.analysis.contradiction',
    'disabled':'text.custodio.analysis.disabled', 'unavailable':'text.custodio.analysis.unavailable',
}
LIMIT_KEYS = {
    'unresolved_scope':'text.custodio.limit.scope', 'unresolved_exception':'text.custodio.limit.exception',
    'conditional_rule_requires_review':'text.custodio.limit.condition',
    'cross_reference_requires_review':'text.custodio.limit.reference',
    'ambiguous_normative':'text.custodio.limit.normative', 'missing_prohibition':'text.custodio.limit.normative',
    'obligation_requires_review':'text.custodio.limit.obligation',
    'human_review_only':'text.custodio.limit.human', 'contradictory_rules':'text.custodio.limit.contradiction',
    'untrusted_rule_instruction':'text.custodio.limit.instruction',
    'invalid_interpretation':'text.custodio.limit.invalid',
    'free_provider_not_configured':'text.custodio.limit.provider_config',
    'invalid_api_key':'text.custodio.limit.provider_key',
    'rate_limited':'text.custodio.limit.quota',
    'analysis_budget_wait':'text.custodio.limit.quota',
    'analysis_daily_limit':'text.custodio.limit.quota',
    'analysis_budget_exceeded':'text.custodio.limit.size',
    'invalid_request':'text.custodio.limit.provider_request',
}
REASONS = {
    'incorrect':'text.custodio.correction.incorrect','allowed':'text.custodio.correction.allowed',
    'exception':'text.custodio.correction.exception','false_positive':'text.custodio.correction.false_positive',
    'ambiguous':'text.custodio.correction.ambiguous','disable':'text.custodio.correction.disable',
    'restore':'text.custodio.correction.restore',
}
NORMATIVE_KEYS = {
    'prohibition':'text.custodio.normative.prohibition','restriction':'text.custodio.normative.restriction',
    'obligation':'text.custodio.normative.obligation','permission':'text.custodio.normative.permission',
    'none':'text.custodio.normative.none','ambiguous':'text.custodio.normative.ambiguous',
}
SCOPE_KEYS = {'all':'text.custodio.scope.all','outside_allowed_channels':'text.custodio.scope.outside',
              'only_listed_channels':'text.custodio.scope.only','ambiguous':'text.custodio.scope.ambiguous'}


def administrator(interaction):
    return bool(interaction.guild and (interaction.user.id == interaction.guild.owner_id
                or interaction.user.guild_permissions.administrator))


class CustodioDetectionView(discord.ui.View):
    @_i18n_context
    def __init__(self,parent,snapshot):
        super().__init__(timeout=600)
        self.parent,self.snapshot = parent,snapshot
        self.guild_id,self.owner_id = parent.guild_id,parent.owner_id
        self.busy = False
        self.read_saved()
        for name,key,style,row in (
            ('analyze','text.ba4c0deba27b34',discord.ButtonStyle.primary,0),
            ('review','text.custodio.analysis.review',discord.ButtonStyle.secondary,0),
            ('correct','text.custodio.analysis.correct',discord.ButtonStyle.primary,0),
            ('save','text.14bdfaf2face3a',discord.ButtonStyle.success,1),
            ('discard','text.80ca383e9c8d3e',discord.ButtonStyle.danger,1),
            ('back','text.ab26ae7bca3621',discord.ButtonStyle.secondary,1)):
            button=discord.ui.Button(label=_t(key),style=style,row=row)
            button.callback=getattr(self,name)
            setattr(self,name+'_button',button)
            self.add_item(button)
        self.sync()

    def read_saved(self):
        self.original=self.parent.get_setting(self.guild_id,KEY)
        self.original_plan=self.parent.get_setting(self.guild_id,PLAN_KEY)
        self.saved=InterpretationPlan.decode(self.original_plan,self.snapshot)
        self.pending=self.saved

    def is_stale(self):
        return (self.original != self.parent.get_setting(self.guild_id,KEY)
            or self.original_plan != self.parent.get_setting(self.guild_id,PLAN_KEY))

    async def interaction_check(self,interaction):
        return await self.parent.access_check(interaction,self.guild_id,self.owner_id)

    def sync(self):
        for child in self.children:
            child.disabled=self.busy
        self.review_button.disabled=self.busy or self.pending is None
        self.correct_button.disabled=self.busy or self.pending is None
        self.save_button.disabled=self.busy or self.pending is None or self.pending==self.saved
        self.discard_button.disabled=self.busy or self.pending==self.saved

    @_i18n_context
    def summary(self):
        counts=Counter(rule.status for rule in self.pending.rules) if self.pending else Counter()
        try:
            enabled=json.loads(self.parent.get_setting(self.guild_id,KEY) or '{}').get('enabled') is True
        except (ValueError,TypeError,AttributeError):
            enabled=False
        return str(_t('text.custodio.analysis.panel',
            state=str(_t('text.custodio.on' if enabled else 'text.custodio.off')),
            total=self.snapshot.count, watchable=counts['watchable'],partial=counts['partial'],
            ambiguous=counts['clarification']+counts['contradiction'],human=counts['unsupported'],
            none=counts['no_prohibition'],disabled=counts['disabled'],unavailable=counts['unavailable'],
            revision=self.snapshot.revision[:12],
            updated=f'<t:{self.pending.created_at}:F>' if self.pending else str(_t('common.none_sentence')),
            pending=str(_t('text.custodio.yes' if self.pending!=self.saved else 'text.custodio.no'))))

    async def blocked(self,interaction):
        if self.busy:
            await interaction.response.defer(thinking=False)
            return True
        return False

    @_i18n_context
    async def analyze(self,interaction):
        if not await self.interaction_check(interaction):
            return
        if not administrator(interaction):
            await interaction.response.edit_message(content=self.summary()+'\n\n'+str(_t('text.custodio.ai_admin_only')),view=self,embed=None)
            return
        await interaction.response.defer(thinking=False)
        if self.busy:
            return
        self.busy=True;self.sync()
        await interaction.edit_original_response(content=self.summary()+'\n\n'+str(_t('text.custodio.analysis.running')),view=self,embed=None)
        notice=_t('text.custodio.ai_failed')
        try:
            fresh=await load_server_rules(self.guild_id,os.environ.get('DISCORD_TOKEN',''))
            if fresh.revision != self.snapshot.revision:
                raise ValueError('stale_rules')
            async def progress(done,total):
                await interaction.edit_original_response(content=self.summary()+'\n\n'+str(_t('text.custodio.analysis.progress',done=done,total=total)),view=self,embed=None)
            proposal=await analyze_snapshot(fresh,administrator_requested=True,
                channels={channel.id:channel.name for channel in interaction.guild.text_channels},
                role_ids={role.id for role in interaction.guild.roles},previous=self.pending,on_progress=progress)
            latest=await load_server_rules(self.guild_id,os.environ.get('DISCORD_TOKEN',''))
            if latest.revision != fresh.revision or not administrator(interaction):
                raise ValueError('stale_rules_or_authority')
            self.pending=proposal
            notice=_t('text.custodio.analysis.ready' if any(rule.status!='unavailable' for rule in proposal.rules)
                      else 'text.custodio.ai_failed')
        except Exception:
            pass
        finally:
            self.busy=False;self.sync()
        await interaction.edit_original_response(content=self.summary()+'\n\n'+str(notice),view=self,embed=None)

    async def review(self,interaction):
        if await self.blocked(interaction) or not self.pending:
            return
        view=CustodioInterpretationView(self)
        await interaction.response.edit_message(content=view.summary(),view=view,embed=None)

    async def correct(self,interaction):
        await self.review(interaction)

    @_i18n_context
    async def save(self,interaction):
        if not await self.interaction_check(interaction):
            return
        if not administrator(interaction):
            await interaction.response.edit_message(content=self.summary()+'\n\n'+str(_t('text.custodio.ai_admin_only')),view=self,embed=None)
            return
        await interaction.response.defer(thinking=False)
        if self.busy or self.pending is None or self.pending==self.saved:
            return
        self.busy=True;self.sync()
        notice=_t('text.custodio.save_failed')
        try:
            fresh=await load_server_rules(self.guild_id,os.environ.get('DISCORD_TOKEN',''))
            if fresh.revision != self.snapshot.revision or self.is_stale():
                raise ValueError('stale_draft')
            proposal=self.pending.approve(interaction.user.id)
            plan_raw=proposal.encode(fresh)
            policy=ObservePolicy.rebase(self.original,fresh)
            # El planificador deriva los mecanismos; no requiere selección manual.
            policy=replace(policy,bindings=tuple(replace(binding,kinds=rule.kinds)
                for binding,rule in zip(policy.bindings,proposal.rules)))
            policy_raw=policy.encode(fresh.count)
            if not await self.interaction_check(interaction) or not administrator(interaction):
                return
            if not self.parent.save_atomic(self.guild_id,{KEY:self.original,PLAN_KEY:self.original_plan},
                    {KEY:policy_raw,PLAN_KEY:plan_raw}):
                raise ValueError('stale_draft')
            self.original,self.original_plan=policy_raw,plan_raw
            self.saved=self.pending=proposal
            notice=_t('text.custodio.saved')
        except Exception:
            pass
        finally:
            self.busy=False;self.sync()
        await interaction.edit_original_response(content=self.summary()+'\n\n'+str(notice),view=self,embed=None)

    async def discard(self,interaction):
        if await self.blocked(interaction):
            return
        self.read_saved();self.sync()
        await interaction.response.edit_message(content=self.summary(),view=self,embed=None)

    async def back(self,interaction):
        if await self.blocked(interaction):
            return
        self.parent._sync_controls()
        await interaction.response.edit_message(content=self.parent.summary(),view=self.parent,embed=None)


class CustodioInterpretationView(discord.ui.View):
    @_i18n_context
    def __init__(self,parent):
        super().__init__(timeout=600)
        self.parent=parent;self.guild_id=parent.guild_id;self.owner_id=parent.owner_id
        self.index=self.part=0
        self.rule_select=discord.ui.Select(placeholder=_t('text.428d2d90458fc5'),row=0,
            options=[discord.SelectOption(label=_t('text.custodio.rule_short',number=n),value=str(n-1),
                description=_t('text.custodio.analysis.rule_help')) for n in range(1,parent.snapshot.count+1)])
        self.rule_select.callback=self.choose
        self.add_item(self.rule_select)
        for name,key,style in (
            ('previous','text.custodio.previous',discord.ButtonStyle.secondary),
            ('next','text.custodio.next',discord.ButtonStyle.secondary),
            ('correct','text.custodio.analysis.correct',discord.ButtonStyle.primary),
            ('back','text.ab26ae7bca3621',discord.ButtonStyle.secondary)):
            button=discord.ui.Button(label=_t(key),style=style,row=1)
            button.callback=getattr(self,name);setattr(self,name+'_button',button);self.add_item(button)
        self.sync()

    async def interaction_check(self,interaction):
        return await self.parent.interaction_check(interaction)

    @_i18n_context
    def fragments(self):
        rule=self.parent.pending.rules[self.index]
        source=self.parent.snapshot.rules[self.index]
        def spans(values):
            return '\n'.join(source[start:end] for start,end in values) or str(_t('common.none_sentence'))
        limitations='\n'.join(str(_t(LIMIT_KEYS.get(value,'text.custodio.limit.unavailable'))) for value in rule.limitations)
        content=str(_t('text.custodio.analysis.detail',number=rule.number,
            quote=source,status=str(_t(STATUS_KEYS[rule.status])),
            normative=str(_t(NORMATIVE_KEYS[rule.normative])),scope=str(_t(SCOPE_KEYS[rule.scope])),
            categories=', '.join(str(_t(BEHAVIORS[category].name_key)) for category in rule.categories) or str(_t('common.none_sentence')),
            mechanisms=', '.join(str(_t(KIND_KEYS[kind])) for kind in sorted(rule.kinds)) or str(_t('common.none_sentence')),
            prohibitions=spans(rule.prohibitions),obligations=spans(rule.obligations),permissions=spans(rule.permissions),
            exceptions=spans(rule.exceptions),conditions=spans(rule.conditions),
            references=', '.join(map(str,rule.references)) or str(_t('common.none_sentence')),
            limits=limitations or str(_t('text.custodio.limit.indicator')),
            channels=', '.join(f'<#{cid}>' for cid in rule.channels) or str(_t('common.none_sentence')),
            correction=str(_t(REASONS[rule.correction])) if rule.correction else str(_t('common.none_sentence')),
            note=rule.clarification or str(_t('common.none_sentence'))))
        return tuple(content[n:n+1750] for n in range(0,len(content),1750))

    def sync(self):
        for option in self.rule_select.options:
            option.default=option.value==str(self.index)
        self.previous_button.disabled=self.part==0
        self.next_button.disabled=self.part>=len(self.fragments())-1

    @_i18n_context
    def summary(self):
        parts=self.fragments()
        return parts[self.part]+'\n\n'+str(_t('text.custodio.analysis.page',part=self.part+1,total=len(parts)))

    async def choose(self,interaction):
        self.index=int(self.rule_select.values[0]);self.part=0;self.sync()
        await interaction.response.edit_message(content=self.summary(),view=self,embed=None)

    async def previous(self,interaction):
        self.part=max(0,self.part-1);self.sync()
        await interaction.response.edit_message(content=self.summary(),view=self,embed=None)

    async def next(self,interaction):
        self.part=min(len(self.fragments())-1,self.part+1);self.sync()
        await interaction.response.edit_message(content=self.summary(),view=self,embed=None)

    async def correct(self,interaction):
        view=CustodioCorrectionView(self)
        await interaction.response.edit_message(content=view.summary(),view=view,embed=None)

    async def back(self,interaction):
        self.parent.sync()
        await interaction.response.edit_message(content=self.parent.summary(),view=self.parent,embed=None)


class CustodioCorrectionView(discord.ui.View):
    @_i18n_context
    def __init__(self,parent):
        super().__init__(timeout=600)
        self.parent=parent;self.guild_id=parent.guild_id;self.owner_id=parent.owner_id
        self.reason='';self.note=''
        self.selector=discord.ui.Select(placeholder=_t('text.custodio.correction.select'),row=0,
            options=[discord.SelectOption(label=_t(key),value=value,
                description=_t('text.custodio.correction.restore_help' if value=='restore' else 'text.custodio.correction.help'))
                for value,key in REASONS.items()])
        self.selector.callback=self.choose;self.add_item(self.selector)
        for name,key in (('edit_note','text.custodio.correction.note'),('apply','text.custodio.correction.apply'),('back','text.ab26ae7bca3621')):
            button=discord.ui.Button(label=_t(key),style=discord.ButtonStyle.secondary if name=='back' else discord.ButtonStyle.primary,row=1)
            button.callback=getattr(self,name);setattr(self,name+'_button',button);self.add_item(button)
        self.apply_button.disabled=True

    async def interaction_check(self,interaction):
        return await self.parent.interaction_check(interaction)

    @_i18n_context
    def summary(self):
        return str(_t('text.custodio.correction.panel',number=self.parent.index+1,
            reason=str(_t(REASONS[self.reason])) if self.reason else str(_t('common.none_sentence')),
            note=self.note or str(_t('common.none_sentence'))))

    async def choose(self,interaction):
        self.reason=self.selector.values[0];self.apply_button.disabled=False
        await interaction.response.edit_message(content=self.summary(),view=self,embed=None)

    async def edit_note(self,interaction):
        await interaction.response.send_modal(CustodioCorrectionModal(self))

    @_i18n_context
    async def apply(self,interaction):
        detection=self.parent.parent
        if await detection.blocked(interaction):
            return
        if not administrator(interaction):
            await interaction.response.edit_message(content=self.summary()+'\n\n'+str(_t('text.custodio.ai_admin_only')),view=self,embed=None)
            return
        if self.reason not in REASONS:
            await interaction.response.defer(thinking=False);return
        detection.pending=detection.pending.correct(self.parent.index,reason=self.reason,note=self.note,
                                                     administrator_id=interaction.user.id)
        detection.sync();self.parent.part=0;self.parent.sync()
        await interaction.response.edit_message(content=self.parent.summary(),view=self.parent,embed=None)

    async def back(self,interaction):
        await interaction.response.edit_message(content=self.parent.summary(),view=self.parent,embed=None)


class CustodioCorrectionModal(discord.ui.Modal):
    @_i18n_context
    def __init__(self,parent):
        super().__init__(title=_t('text.custodio.correction.note'),timeout=600)
        self.parent=parent;self.guild_id=parent.guild_id;self.owner_id=parent.owner_id
        self.note_input=discord.ui.TextInput(label=_t('text.custodio.correction.note'),
            placeholder=_t('text.custodio.correction.note_hint'),default=parent.note,
            style=discord.TextStyle.paragraph,required=False,max_length=1000)
        self.add_item(self.note_input)

    async def on_submit(self,interaction):
        if not await self.parent.interaction_check(interaction):
            return
        self.parent.note=self.note_input.value
        await interaction.response.edit_message(content=self.parent.summary(),view=self.parent,embed=None)
