<script lang="ts">
	export let tier: 'public' | 'authenticated' | 'privileged' = 'public';
	export let locked: boolean = false;

	const TIER_CONFIG = {
		public: {
			label: 'Public',
			icon: '🌐',
			bg: 'bg-emerald-100 dark:bg-emerald-900/40',
			text: 'text-emerald-700 dark:text-emerald-300',
			border: 'border-emerald-200 dark:border-emerald-700'
		},
		authenticated: {
			label: 'OSU Login',
			icon: '🎓',
			bg: 'bg-blue-100 dark:bg-blue-900/40',
			text: 'text-blue-700 dark:text-blue-300',
			border: 'border-blue-200 dark:border-blue-700'
		},
		privileged: {
			label: 'Verified',
			icon: '🔒',
			bg: 'bg-amber-100 dark:bg-amber-900/40',
			text: 'text-amber-700 dark:text-amber-300',
			border: 'border-amber-200 dark:border-amber-700'
		}
	} as const;

	$: config = TIER_CONFIG[tier] ?? TIER_CONFIG.public;
</script>

<span
	class="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full border
		{config.bg} {config.text} {config.border}
		{locked ? 'opacity-75' : ''}"
	title="Access tier: {tier}"
>
	<span aria-hidden="true">{config.icon}</span>
	{config.label}
	{#if locked}
		<span aria-label="locked" class="ml-0.5">🔐</span>
	{/if}
</span>
