<script lang="ts">
	import { getContext } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import { goto } from '$app/navigation';

	// 'tier_required' → user needs to log in
	// 'step_up_required' → authenticated user needs elevated verification
	export let code: 'tier_required' | 'step_up_required' = 'tier_required';
	export let requiredTier: string = 'authenticated';

	const i18n = getContext('i18n') as any;
	const dispatch = createEventDispatcher<{ close: void; elevated: { token: string } }>();

	const isStepUp = code === 'step_up_required';

	let verifying = false;
	let verifyError = '';

	async function startStepUp() {
		verifying = true;
		verifyError = '';

		try {
			const res = await fetch('/api/v1/auths/step-up/initiate', {
				method: 'POST',
				headers: { Authorization: `Bearer ${localStorage.token}` }
			});
			if (!res.ok) {
				verifyError = $i18n.t('Step-up verification is not available on this server.');
				return;
			}
			const { authorize_url } = await res.json();

			const popup = window.open(
				authorize_url,
				'stepup',
				'width=500,height=700'
			);

			const onMessage = (evt: MessageEvent) => {
				if (evt.origin !== window.location.origin) return;
				if (evt.data?.type === 'stepup_complete') {
					window.removeEventListener('message', onMessage);
					localStorage.token = evt.data.token;
					dispatch('elevated', { token: evt.data.token });
					dispatch('close');
				} else if (evt.data?.type === 'stepup_error') {
					window.removeEventListener('message', onMessage);
					verifyError = evt.data.message || $i18n.t('Verification failed.');
					verifying = false;
				}
			};
			window.addEventListener('message', onMessage);

			// Fallback: if the popup is closed without a message, stop spinner.
			const poll = setInterval(() => {
				if (popup?.closed) {
					clearInterval(poll);
					window.removeEventListener('message', onMessage);
					verifying = false;
				}
			}, 500);
		} catch {
			verifyError = $i18n.t('Could not start verification. Please try again.');
			verifying = false;
		}
	}
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
				{isStepUp ? $i18n.t('Elevated Access Required') : $i18n.t('OSU Login Required')}
			</h2>
		</div>

		{#if isStepUp}
			<p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
				{$i18n.t('This agent requires step-up verification to protect sensitive university data (e.g., student records or financial aid).')}
			</p>
			{#if verifyError}
				<div class="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 px-3 py-2 text-xs text-red-700 dark:text-red-300 mb-4">
					{verifyError}
				</div>
			{/if}
		{:else}
			<p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
				{$i18n.t('This agent requires an active OSU login. Please sign in with your Oregon State University account to continue.')}
			</p>
		{/if}

		<div class="flex justify-end gap-2">
			<button
				class="px-4 py-2 rounded-lg text-sm hover:bg-gray-100 dark:hover:bg-gray-800 transition"
				disabled={verifying}
				on:click={() => dispatch('close')}
			>
				{$i18n.t('Dismiss')}
			</button>
			{#if isStepUp}
				<button
					class="px-4 py-2 rounded-lg text-sm font-medium text-white transition disabled:opacity-50"
					style="background: #DC4405;"
					disabled={verifying}
					on:click={startStepUp}
				>
					{verifying ? $i18n.t('Verifying…') : $i18n.t('Verify Identity')}
				</button>
			{:else}
				<button
					class="px-4 py-2 rounded-lg text-sm font-medium text-white transition"
					style="background: #DC4405;"
					on:click={() => { dispatch('close'); goto('/auth'); }}
				>
					{$i18n.t('Sign in with OSU')}
				</button>
			{/if}
		</div>
	</div>
</div>
