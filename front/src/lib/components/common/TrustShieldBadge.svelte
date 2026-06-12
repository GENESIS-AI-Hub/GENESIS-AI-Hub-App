<script lang="ts">
	export let tier: 'public' | 'authenticated' | 'privileged' = 'public';
	export let locked: boolean = false;

	const TIER_CONFIG = {
		public: {
			label: 'Provisional',
			icon: '⚠️',
			bg: 'bg-red-100 dark:bg-red-900/40',
			text: 'text-red-700 dark:text-red-300',
			border: 'border-red-200 dark:border-red-700'
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
			icon: '✅',
			bg: 'bg-green-100 dark:bg-green-900/40',
			text: 'text-green-700 dark:text-green-300',
			border: 'border-green-200 dark:border-green-700'
		}
	} as const;

	$: config = TIER_CONFIG[tier] ?? TIER_CONFIG.public;
</script>

<span
	class="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full border
		{config.bg} {config.text} {config.border}
		{locked ? 'opacity-75' : ''}"
	title="Trust status: {config.label}"
>
	<span aria-hidden="true">{config.icon}</span>
	{config.label}
	{#if locked}
		<span aria-label="locked" class="ml-0.5">🔐</span>
	{/if}
</span>
