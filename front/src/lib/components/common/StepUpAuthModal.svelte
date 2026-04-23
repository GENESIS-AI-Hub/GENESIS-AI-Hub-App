<script lang="ts">
	import { getContext } from 'svelte';
	import { createEventDispatcher } from 'svelte';

	// 'tier_required' → user needs to log in
	// 'step_up_required' → authenticated user needs elevated verification
	export let code: 'tier_required' | 'step_up_required' = 'tier_required';
	export let requiredTier: string = 'authenticated';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher<{ close: void }>();

	const isStepUp = code === 'step_up_required';
</script>

<!-- Step-up / tier-required modal overlay -->
<div
	class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
	role="dialog"
	aria-modal="true"
	aria-labelledby="stepup-title"
>
	<div class="bg-white dark:bg-gray-900 rounded-2xl p-6 w-full max-w-sm shadow-2xl border border-gray-200 dark:border-gray-700">
		<!-- OSU Beaver Orange accent bar -->
		<div class="h-1 w-full rounded-full mb-5" style="background: #DC4405;" />

		<div class="flex items-center gap-3 mb-4">
			<span class="text-3xl" aria-hidden="true">{isStepUp ? '🔒' : '🎓'}</span>
			<h2 id="stepup-title" class="text-lg font-semibold text-gray-900 dark:text-white">
				{isStepUp ? 'Elevated Access Required' : 'OSU Login Required'}
			</h2>
		</div>

		{#if isStepUp}
			<p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
				This agent requires step-up verification to protect sensitive university data
				(e.g., student records or financial aid).
			</p>
			<div class="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 px-3 py-2 text-xs text-amber-700 dark:text-amber-300 mb-4">
				<!-- TODO(#143): Wire real MFA step-up flow once OSU OIDC integration lands -->
				Step-up verification coming soon — tracked in <strong>#143</strong>.
			</div>
		{:else}
			<p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
				This agent requires an active OSU login. Please sign in with your
				Oregon State University account to continue.
			</p>
		{/if}

		<div class="flex justify-end gap-2">
			<button
				class="px-4 py-2 rounded-lg text-sm hover:bg-gray-100 dark:hover:bg-gray-800 transition"
				on:click={() => dispatch('close')}
			>
				Dismiss
			</button>
			{#if !isStepUp}
				<button
					class="px-4 py-2 rounded-lg text-sm font-medium text-white transition"
					style="background: #DC4405;"
					on:click={() => dispatch('close')}
				>
					Sign in with OSU
				</button>
			{/if}
		</div>
	</div>
</div>
