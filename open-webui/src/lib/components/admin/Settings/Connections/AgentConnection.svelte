<script lang="ts">
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Cog6 from '$lib/components/icons/Cog6.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import { toast } from 'svelte-sonner';
	import { verifyA2AAgentConnection } from '$lib/apis/configs';

	export let onDelete = () => {};
	export let onSubmit = () => {};

	export let url = '';
	export let name = '';
	export let config = {};

	let showDeleteConfirmDialog = false;
	let verifying = false;
	let verified = false;
	let agentInfo = null;

	const verifyConnection = async () => {
		if (!url || !url.trim()) {
			toast.error($i18n.t('Please enter a valid agent URL'));
			return;
		}

		verifying = true;
		verified = false;

		try {
			const res = await verifyA2AAgentConnection(localStorage.token, { url, name, config });
			if (res && res.success) {
				verified = true;
				agentInfo = res.agent_info;

				// Update URL with normalized version from server
				if (res.url) {
					url = res.url;
				}

				// Auto-fill name if not set
				if (agentInfo && agentInfo.name && !name) {
					name = agentInfo.name;
				}

				toast.success($i18n.t('Agent connection verified successfully'));
			} else {
				verified = false;
				toast.error($i18n.t('Failed to verify agent connection'));
			}
		} catch (error) {
			verified = false;
			console.error('Error verifying agent connection:', error);
			const errorMessage = error?.detail || error?.message || 'Failed to verify agent connection';
			toast.error($i18n.t(errorMessage));
		} finally {
			verifying = false;
		}
	};
</script>

<ConfirmDialog
	bind:show={showDeleteConfirmDialog}
	on:confirm={() => {
		onDelete();
	}}
/>

<div class="flex w-full gap-2 items-center">
	<div class="flex w-full gap-2">
		<Tooltip
			className="flex-1 relative"
			content={$i18n.t(`Agent URL (e.g., localhost:8000 or http://localhost:8000)`)}
			placement="top-start"
		>
			<input
				class="outline-hidden w-full bg-transparent"
				placeholder={$i18n.t('Agent URL')}
				bind:value={url}
				autocomplete="off"
				on:blur={() => {
					if (url && !verified) {
						verifyConnection();
					}
				}}
			/>
		</Tooltip>

		<Tooltip
			className="flex-1 relative"
			content={$i18n.t(`Custom name for the agent (auto-filled after verification)`)}
			placement="top-start"
		>
			<input
				class="outline-hidden w-full bg-transparent"
				placeholder={$i18n.t('Agent Name (optional)')}
				bind:value={name}
				autocomplete="off"
			/>
		</Tooltip>
	</div>

	<div class="flex gap-1 items-center">
		{#if verified}
			<Tooltip content={$i18n.t('Agent verified')}>
				<div class="p-1 text-green-500">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="2"
						stroke="currentColor"
						class="size-4"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
				</div>
			</Tooltip>
		{:else if verifying}
			<div class="p-1">
				<svg
					class="size-4 animate-spin"
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
				>
					<circle
						class="opacity-25"
						cx="12"
						cy="12"
						r="10"
						stroke="currentColor"
						stroke-width="4"
					/>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
					/>
				</svg>
			</div>
		{/if}

		<Tooltip content={$i18n.t('Verify Connection')} className="self-start">
			<button
				class="self-center p-1 bg-transparent hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 rounded-lg transition"
				on:click={verifyConnection}
				disabled={verifying || !url}
				type="button"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="size-4"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
					/>
				</svg>
			</button>
		</Tooltip>

		<Tooltip content={$i18n.t('Delete')} className="self-start">
			<button
				class="self-center p-1 bg-transparent hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 rounded-lg transition"
				on:click={() => {
					showDeleteConfirmDialog = true;
				}}
				type="button"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="size-4"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
					/>
				</svg>
			</button>
		</Tooltip>
	</div>
</div>
