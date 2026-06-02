<script lang="ts">
	export let open = false;
	export let agentName = '';
	export let onConfirm: () => void = () => {};
	export let onCancel: () => void = () => {};

	function handleKeydown(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === 'Escape') onCancel();
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if open}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
		role="dialog"
		aria-modal="true"
		aria-labelledby="provisional-modal-title"
	>
		<div class="bg-white dark:bg-gray-900 rounded-xl shadow-xl max-w-sm w-full mx-4 p-6">
			<div class="flex items-start gap-3 mb-4">
				<div class="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/40 flex items-center justify-center">
					<span class="text-lg" aria-hidden="true">⚠️</span>
				</div>
				<div>
					<h2
						id="provisional-modal-title"
						class="text-base font-semibold text-gray-900 dark:text-gray-100"
					>
						Unverified Agent
					</h2>
					<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
						<strong class="text-gray-900 dark:text-gray-100">"{agentName}"</strong> has not been reviewed
						by OSU administration. Messages you send may not be subject to OSU's standard data protections.
					</p>
				</div>
			</div>

			<div class="flex gap-2 justify-end mt-2">
				<button
					class="px-4 py-2 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition"
					on:click={onCancel}
				>
					Cancel
				</button>
				<button
					class="px-4 py-2 text-sm rounded-lg bg-red-600 hover:bg-red-700 text-white font-medium transition"
					on:click={onConfirm}
				>
					Proceed anyway
				</button>
			</div>
		</div>
	</div>
{/if}
