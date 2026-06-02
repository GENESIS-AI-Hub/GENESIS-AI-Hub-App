<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import { WEBUI_NAME, user, models } from '$lib/stores';
	import { getModels } from '$lib/apis';
	import { WEBUI_BASE_URL } from '$lib/constants';

	import {
		type RegistryAgent,
		getRegistryAgents,
		getFeaturedAgents,
		submitRegistryAgent,
		updateRegistryAgent,
		deleteRegistryAgent,
		clearRegistry
	} from '$lib/apis/registry';

	import { updateAgent } from '$lib/apis/agents';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import ArrowDownTray from '$lib/components/icons/ArrowDownTray.svelte';
	import TrustShieldBadge from '$lib/components/common/TrustShieldBadge.svelte';
	import StepUpAuthModal from '$lib/components/common/StepUpAuthModal.svelte';

	const i18n = getContext('i18n');

	let loaded = false;
	let agents: RegistryAgent[] = [];
	let featuredAgents: RegistryAgent[] = [];
	let filteredAgents: RegistryAgent[] = [];
	let searchValue = '';

	let localAgents = [];

	// Step-up / tier-required modal state
	let stepUpModal: { code: 'tier_required' | 'step_up_required'; requiredTier: string } | null =
		null;

	/** Unix timestamp (ms) until which the user holds a step-up elevated session.
	 *  Set when the step-up OAuth popup completes successfully. */
	let elevatedUntilMs: number | null = null;

	function onElevated(evt: CustomEvent<{ token: string }>) {
		// Token already stored in localStorage by the modal.
		// Parse the elevated_until claim to know how long elevation lasts.
		try {
			const payload = JSON.parse(atob(evt.detail.token.split('.')[1]));
			if (payload.elevated_until) {
				elevatedUntilMs = payload.elevated_until * 1000; // convert epoch seconds → ms
			}
		} catch {
			elevatedUntilMs = Date.now() + 30 * 60 * 1000; // fallback: 30 min
		}
	}

	/** Scope the current user holds: public < authenticated < privileged */
	$: baseScope = $user?.role === 'admin'
		? 'privileged'
		: $user?.role === 'user'
			? 'authenticated'
			: 'public';

	$: userScope =
		elevatedUntilMs && Date.now() < elevatedUntilMs ? 'privileged' : baseScope;

	const TIER_ORDER: Record<string, number> = { public: 0, authenticated: 1, privileged: 2 };

	function canAccessAgent(agent: { trust_tier?: string | null }): boolean {
		const required = TIER_ORDER[agent.trust_tier ?? 'public'] ?? 0;
		const available = TIER_ORDER[userScope] ?? 0;
		return available >= required;
	}

	const fetchLocalAgents = async () => {
		try {
			const res = await fetch(`${WEBUI_BASE_URL}/api/v1/agents/`, {
				headers: { 'Authorization': `Bearer ${localStorage.token}` }
			});
			if (res.ok) {
				localAgents = await res.json();
			} else {
				toast.error('Failed to fetch local agents');
			}
		} catch (e) {
			toast.error('Failed to fetch local agents');
		}
	};

	const deleteLocalAgent = async (id) => {
		try {
			const res = await fetch(`${WEBUI_BASE_URL}/api/v1/agents/${id}`, {
				method: 'DELETE',
				headers: { 'Authorization': `Bearer ${localStorage.token}` }
			});
			if (res.ok) {
				toast.success('Agent deleted');
				models.set(await getModels(localStorage.token));
				await fetchLocalAgents();
			} else {
				toast.error('Failed to delete agent');
			}
		} catch (e) {
			toast.error('Failed to delete agent');
		}
	};


	const setLocalAgentTier = async (id: string, tier: 'public' | 'privileged') => {
		try {
			await updateAgent(localStorage.token as string, id, { trust_tier: tier });
			toast.success(tier === 'privileged' ? 'Agent marked as Verified' : 'Agent marked as Provisional');
			await fetchLocalAgents();
		} catch {
			toast.error('Failed to update trust status');
		}
	};

	let showAddModal = false;
	let addUrl = '';
	let addImageUrl = '';
	let addSubmitting = false;

	let showClearConfirm = false;
	let clearSubmitting = false;

	const handleClearRegistry = async () => {
		clearSubmitting = true;
		try {
			const { deleted } = await clearRegistry(localStorage.token as string);
			toast.success($i18n.t('Registry cleared ({{count}} agents removed)', { count: deleted }));
			showClearConfirm = false;
			await refreshAgents();
			models.set(await getModels(localStorage.token as string));
		} catch (e) {
			toast.error(e instanceof Error ? e.message : $i18n.t('Failed to clear registry'));
		} finally {
			clearSubmitting = false;
		}
	};

	$: filteredAgents = agents.filter(
		(a) => searchValue === '' || a.name.toLowerCase().includes(searchValue.toLowerCase())
	);

	const isPublic = (agent: RegistryAgent): boolean => agent.access_control === null;

	const isOwnerOrAdmin = (agent: RegistryAgent): boolean =>
		$user?.role === 'admin' || agent.user_id === $user?.id;

	const refreshAgents = async () => {
		const token = localStorage.token as string;
		[agents, featuredAgents] = await Promise.all([
			getRegistryAgents(token),
			getFeaturedAgents(token)
		]);
		await fetchLocalAgents();
	};

	const handleInstall = async (agent: RegistryAgent) => {
		const installUrl = agent.card_url || agent.url;
		if (!installUrl) {
			toast.error($i18n.t('No URL available to install this agent.'));
			return;
		}

		try {
			const res = await fetch(`${WEBUI_BASE_URL}/api/v1/agents/register-by-url`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${localStorage.token}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					agent_url: installUrl,
					profile_image_url: agent.image_url
				})
			});

			if (res.ok) {
				toast.success($i18n.t('Agent installed'));
				models.set(await getModels(localStorage.token as string));
			} else {
				const err = await res.json().catch(() => ({}));
				if (res.status === 403 && err.detail?.code) {
					stepUpModal = {
						code: err.detail.code,
						requiredTier: err.detail.required_tier ?? 'authenticated'
					};
				} else {
					toast.error((err as { detail?: string }).detail ?? $i18n.t('Failed to install agent'));
				}
			}
		} catch {
			toast.error($i18n.t('Failed to install agent'));
		}
	};

	const handleDelete = async (agent: RegistryAgent) => {
		try {
			await deleteRegistryAgent(localStorage.token as string, agent.id);
			toast.success($i18n.t('Agent removed from registry'));
			await refreshAgents();
			models.set(await getModels(localStorage.token as string));
		} catch {
			toast.error($i18n.t('Failed to delete agent'));
		}
	};

	const handleTogglePublic = async (agent: RegistryAgent) => {
		try {
			const newAccessControl = isPublic(agent) ? {} : null;
			await updateRegistryAgent(localStorage.token as string, agent.id, {
				access_control: newAccessControl
			});
			toast.success(isPublic(agent) ? $i18n.t('Agent set to private') : $i18n.t('Agent is now public'));
			await refreshAgents();
		} catch (e) {
			toast.error(e instanceof Error ? e.message : $i18n.t('Failed to update visibility'));
		}
	};

	const handleToggleFeatured = async (agent: RegistryAgent) => {
		if (!isPublic(agent) && !agent.is_featured) {
			toast.error($i18n.t('Agent must be public before it can be featured'));
			return;
		}
		try {
			await updateRegistryAgent(localStorage.token as string, agent.id, {
				is_featured: !agent.is_featured
			});
			toast.success(agent.is_featured ? $i18n.t('Agent unfeatured') : $i18n.t('Agent featured'));
			await refreshAgents();
		} catch (e) {
			toast.error(e instanceof Error ? e.message : $i18n.t('Failed to update featured status'));
		}
	};

	onMount(async () => {
		await refreshAgents();
		loaded = true;
	});

	const handleAddAgent = async () => {
		if (!addUrl || addSubmitting) return;
		addSubmitting = true;
		try {
			await submitRegistryAgent(localStorage.token as string, addUrl.trim(), addImageUrl.trim() || undefined);
			toast.success($i18n.t('Agent added to registry'));
			showAddModal = false;
			addUrl = '';
			addImageUrl = '';
			await refreshAgents();
			models.set(await getModels(localStorage.token as string));
		} catch (e) {
			toast.error(e instanceof Error ? e.message : $i18n.t('Failed to add agent'));
		} finally {
			addSubmitting = false;
		}
	};

	function onImageError(e: Event) {
		(e.target as HTMLImageElement).src = '/static/favicon.png';
	}
</script>

<svelte:head>
	<title>
		{$i18n.t('Agents')} | {$WEBUI_NAME}
	</title>
</svelte:head>

{#if stepUpModal}
	<StepUpAuthModal
		code={stepUpModal.code}
		requiredTier={stepUpModal.requiredTier}
		on:close={() => (stepUpModal = null)}
		on:elevated={onElevated}
	/>
{/if}

{#if loaded}
	<!-- Clear Registry Confirm Modal -->
	{#if showClearConfirm}
		<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
			<div class="bg-white dark:bg-gray-900 rounded-2xl p-6 w-full max-w-sm shadow-xl">
				<h2 class="text-lg font-semibold mb-2">{$i18n.t('Clear Registry?')}</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
					{$i18n.t('This will permanently delete every agent from the registry. This cannot be undone.')}
				</p>
				<div class="flex justify-end gap-2">
					<button
						class="px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
						on:click={() => (showClearConfirm = false)}
					>
						{$i18n.t('Cancel')}
					</button>
					<button
						class="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-medium disabled:opacity-50"
						disabled={clearSubmitting}
						on:click={handleClearRegistry}
					>
						{clearSubmitting ? $i18n.t('Clearing...') : $i18n.t('Clear All')}
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- Add Agent Modal -->
	{#if showAddModal}
		<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
			<div class="bg-white dark:bg-gray-900 rounded-2xl p-6 w-full max-w-md shadow-xl">
				<h2 class="text-xl font-semibold mb-4">{$i18n.t('Add Agent to Registry')}</h2>

				<div class="mb-4">
					<label class="block text-sm font-medium mb-1">{$i18n.t('Agent URL')}</label>
					<input
						type="text"
						bind:value={addUrl}
						placeholder="http://localhost:8002"
						class="w-full px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
					/>
					<p class="text-xs text-gray-500 mt-1">
						{$i18n.t('URL must host a .well-known/agent.json file')}
					</p>
				</div>

				<div class="mb-6">
					<label class="block text-sm font-medium mb-1">
						{$i18n.t('Agent Image URL (Optional)')}
					</label>
					<input
						type="text"
						bind:value={addImageUrl}
						placeholder="https://example.com/image.png"
						class="w-full px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
					/>
				</div>

				<p class="text-xs text-gray-500 mb-4">
					{$i18n.t('New agents are private by default. You can make them public after adding.')}
				</p>

				<div class="flex justify-end gap-2">
					<button
						class="px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
						on:click={() => {
							showAddModal = false;
							addUrl = '';
							addImageUrl = '';
						}}
					>
						{$i18n.t('Cancel')}
					</button>
					<button
						class="px-4 py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black font-medium disabled:opacity-50"
						disabled={!addUrl || addSubmitting}
						on:click={handleAddAgent}
					>
						{addSubmitting ? $i18n.t('Adding...') : $i18n.t('Add')}
					</button>
				</div>
			</div>
		</div>
	{/if}

	<div class="flex flex-col gap-1 my-1.5">
		<div class="flex justify-between items-center">
			<div class="flex items-center md:self-center text-xl font-medium px-0.5">
				{$i18n.t('Agents')}
				<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />
				<span class="text-lg font-medium text-gray-500 dark:text-gray-300">
					{filteredAgents.length}
				</span>
			</div>
		</div>

		<div class="flex flex-1 items-center w-full space-x-2">
			<div class="flex flex-1 items-center">
				<div class="self-center ml-1 mr-3">
					<Search className="size-3.5" />
				</div>
				<input
					class="w-full text-sm py-1 rounded-r-xl outline-hidden bg-transparent"
					bind:value={searchValue}
					placeholder={$i18n.t('Search Agents')}
				/>
			</div>

			<div class="flex items-center gap-1">
				{#if $user?.role === 'admin'}
					<a
						href="/workspace/agents/deploy"
						class="px-3 py-2 rounded-xl bg-black dark:bg-white text-white dark:text-black hover:opacity-80 transition font-medium text-xs"
					>
						{$i18n.t('Deploy new agent')}
					</a>
					<Tooltip content={$i18n.t('Clear all registry agents')}>
						<button
							class="px-2 py-2 rounded-xl hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 transition text-xs font-medium"
							on:click={() => (showClearConfirm = true)}
						>
							{$i18n.t('Clear Registry')}
						</button>
					</Tooltip>
				{/if}
				<button
					class="px-2 py-2 rounded-xl hover:bg-gray-700/10 dark:hover:bg-gray-100/10 dark:text-gray-300 dark:hover:text-white transition font-medium text-sm flex items-center space-x-1"
					on:click={() => (showAddModal = true)}
				>
					<Plus className="size-3.5" />
				</button>
			</div>
		</div>
	</div>

	<!-- Featured Agents Section -->
	{#if featuredAgents.length > 0 && searchValue === ''}
		<div class="mb-6">
			<div class="flex items-center gap-2 mb-3">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="currentColor"
					class="size-4 text-amber-500"
				>
					<path
						fill-rule="evenodd"
						d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.006 5.404.434c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.434 2.082-5.006Z"
						clip-rule="evenodd"
					/>
				</svg>
				<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
					{$i18n.t('Featured')}
				</h2>
			</div>

			<div class="gap-2 grid lg:grid-cols-2 xl:grid-cols-3">
				{#each featuredAgents as agent}
					<div
						class="flex flex-col w-full px-3 py-2 rounded-xl transition border border-amber-200 dark:border-amber-800 bg-amber-50/60 dark:bg-amber-900/10 hover:border-amber-400 dark:hover:border-amber-600"
					>
						<div class="flex gap-4 mt-0.5 mb-0.5">
							<div class="w-[44px] shrink-0">
								<div class="rounded-full object-cover">
									<img
										src={agent.image_url ?? '/static/favicon.png'}
										alt="agent profile"
										class="rounded-full w-full h-auto object-cover"
										on:error={(e) => {
											if (e.target instanceof HTMLImageElement)
												e.target.src = '/static/favicon.png';
										}}
									/>
								</div>
							</div>

							<div class="flex flex-col flex-1 min-w-0">
								<div class="flex justify-between items-start">
									<div class="flex items-center gap-1.5 min-w-0">
										<div class="font-semibold line-clamp-1 break-all" title={agent.name}>
											{agent.name}
										</div>
										<span
											class="shrink-0 text-[9px] px-1.5 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-700 font-medium"
										>
											{$i18n.t('Featured')}
										</span>
									</div>

									<div class="flex items-center gap-1">
										<Tooltip content={$i18n.t('Install')}>
											<button
												class="p-1.5 rounded-lg hover:bg-amber-200 dark:hover:bg-amber-800 transition text-gray-600 dark:text-gray-300"
												on:click={() => handleInstall(agent)}
											>
												<ArrowDownTray className="size-4" />
											</button>
										</Tooltip>

										{#if isOwnerOrAdmin(agent)}
											{#if $user?.role === 'admin'}
												<Tooltip content={$i18n.t('Unfeature')}>
													<button
														class="p-1.5 rounded-lg hover:bg-amber-200 dark:hover:bg-amber-800 transition text-amber-500"
														on:click={() => handleToggleFeatured(agent)}
													>
														<svg
															xmlns="http://www.w3.org/2000/svg"
															viewBox="0 0 24 24"
															fill="currentColor"
															class="size-4"
														>
															<path
																fill-rule="evenodd"
																d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.006 5.404.434c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.434 2.082-5.006Z"
																clip-rule="evenodd"
															/>
														</svg>
													</button>
												</Tooltip>
											{/if}

											<Tooltip content={$i18n.t('Delete')}>
												<button
													class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 transition"
													on:click={() => handleDelete(agent)}
												>
													<GarbageBin className="size-4" />
												</button>
											</Tooltip>
										{/if}
									</div>
								</div>

								<div
									class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mt-1"
									title={agent.description ?? ''}
								>
									{agent.description || $i18n.t('No description')}
								</div>

								<div class="mt-2 flex flex-wrap gap-1">
									{#if agent.foundational_model}
										<span
											class="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
										>
											{agent.foundational_model}
										</span>
									{/if}
									{#if agent.tools?.capabilities}
										{#each Object.keys(agent.tools.capabilities) as cap}
											<span
												class="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
											>
												{cap}
											</span>
										{/each}
									{/if}
								</div>
							</div>
						</div>

						<div
							class="mt-2 pt-2 border-t border-amber-100 dark:border-amber-900 flex justify-between items-center text-xs text-gray-500"
						>
							<div class="truncate max-w-[200px]" title={agent.url}>{agent.url}</div>
						</div>
					</div>
				{/each}
			</div>

			<div class="mt-4 mb-2 w-full h-px bg-gray-100 dark:bg-gray-800" />
		</div>
	{/if}


	{#if localAgents.length > 0}
		<div class="mb-6 mt-6">
			<div class="flex items-center gap-2 mb-3">
				<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
					{$i18n.t('Installed Agents')}
				</h2>
			</div>
			<div class="gap-2 grid lg:grid-cols-2 xl:grid-cols-3">
				{#each localAgents as agent}
					<div
						class="flex flex-col w-full px-3 py-2 dark:bg-white/5 bg-black/5 rounded-xl transition border border-transparent hover:border-gray-200 dark:hover:border-gray-700"
					>
						<div class="flex gap-4 mt-0.5 mb-0.5">
							<div class="w-[44px] shrink-0">
								<div class="rounded-full object-cover">
									<img
										src={agent.profile_image_url ?? agent.image_url ?? '/static/favicon.png'}
										alt="agent profile"
										class="rounded-full w-full h-auto object-cover"
										on:error={(e) => {
											if (e.target instanceof HTMLImageElement) e.target.src = '/static/favicon.png';
										}}
									/>
								</div>
							</div>

							<div class=" flex flex-col flex-1 min-w-0">
								<div class="flex justify-between items-start">
									<div class="font-semibold line-clamp-1 break-all" title={agent.name}>{agent.name}</div>
									
									<!-- Actions -->
									<div class="flex items-center gap-1">
										{#if $user?.role === 'admin' && agent.endpoint && agent.deployment_mode !== 'internal'}
											{#if agent.trust_tier === 'privileged'}
												<Tooltip content="Revoke verification (mark Provisional)">
													<button
														class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500 transition text-xs font-bold"
														on:click={() => setLocalAgentTier(agent.id, 'public')}
														aria-label="Revoke verification"
													>⚠️</button>
												</Tooltip>
											{:else}
												<Tooltip content="Mark as Verified">
													<button
														class="p-1.5 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 text-green-600 transition text-xs font-bold"
														on:click={() => setLocalAgentTier(agent.id, 'privileged')}
														aria-label="Mark as Verified"
													>✅</button>
												</Tooltip>
											{/if}
										{/if}
										{#if $user?.role === 'admin' || agent.user_id === $user?.id}
											<Tooltip content={$i18n.t('Delete')}>
												<button
													class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 transition"
													on:click={() => deleteLocalAgent(agent.id)}
												>
													<GarbageBin className="size-4" />
												</button>
											</Tooltip>
										{/if}
									</div>
								</div>

								<div class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mt-1" title={agent.description}>
									{agent.description || $i18n.t('No description')}
								</div>
								
								<div class="mt-2 flex flex-wrap gap-1">
									{#if agent.endpoint && agent.deployment_mode !== 'internal'}
										<TrustShieldBadge
											tier={agent.trust_tier ?? 'public'}
											locked={!canAccessAgent(agent)}
										/>
									{/if}
									{#if agent.model || agent.foundational_model}
										<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
											{agent.model ?? agent.foundational_model}
										</span>
									{/if}
									{#if agent.deployment_mode}
										<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
											{agent.deployment_mode}
										</span>
									{/if}
									{#if agent.capabilities}
										{#each Object.keys(agent.capabilities) as cap}
											<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
												{cap}
											</span>
										{/each}
									{/if}
								</div>
							</div>
						</div>
						
						<div class="mt-2 pt-2 border-t border-gray-100 dark:border-gray-800 flex justify-between items-center text-xs text-gray-500">
							<div class="truncate max-w-[260px]" title={agent.endpoint ?? agent.url}>{agent.endpoint ?? agent.url}</div>
						</div>
					</div>
				{/each}
			</div>
			<div class="mt-4 mb-2 w-full h-px bg-gray-100 dark:bg-gray-800" />
		</div>
	{/if}


	<div class="flex items-center gap-2 mb-3"><h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">{$i18n.t('Registry Agents')}</h2></div>
	<!-- All Agents Grid -->
	<div class="my-2 mb-5 gap-2 grid lg:grid-cols-2 xl:grid-cols-3" id="agent-list">
		{#each filteredAgents as agent}
			{@const accessible = canAccessAgent(agent)}
			<div
				class="relative flex flex-col w-full px-3 py-2 dark:bg-white/5 bg-black/5 rounded-xl transition border
					{accessible
						? 'border-transparent hover:border-gray-200 dark:hover:border-gray-700'
						: 'border-gray-200 dark:border-gray-700 opacity-80'}"
			>
				<!-- Locked overlay for inaccessible agents -->
				{#if !accessible}
					<div
						class="absolute inset-0 rounded-xl bg-gray-50/60 dark:bg-gray-900/60 flex items-center justify-center z-10 cursor-pointer"
						title="Your account does not have access to this agent"
						role="button"
						tabindex="0"
						on:click={() => handleInstall(agent)}
						on:keydown={(e) => e.key === 'Enter' && handleInstall(agent)}
					>
						<div class="flex flex-col items-center gap-1 text-gray-500 dark:text-gray-400">
							<span class="text-2xl">🔐</span>
							<span class="text-xs font-medium">Access restricted</span>
						</div>
					</div>
				{/if}

				<div class="flex gap-4 mt-0.5 mb-0.5">
					<div class="w-[44px] shrink-0">
						<div class="rounded-full object-cover">
							<img
								src={agent.image_url ?? '/static/favicon.png'}
								alt="agent profile"
								class="rounded-full w-full h-auto object-cover"
								on:error={onImageError}
							/>
						</div>
					</div>

					<div class="flex flex-col flex-1 min-w-0">
						<div class="flex justify-between items-start gap-1">
							<div class="flex items-center gap-1.5 min-w-0">
								<div class="font-semibold line-clamp-1 break-all" title={agent.name}>
									{agent.name}
								</div>
								{#if isPublic(agent)}
									<Tooltip content={$i18n.t('Public — visible to all users')}>
										<span class="shrink-0 text-[9px] px-1.5 py-0.5 rounded-full bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800 font-medium">
											{$i18n.t('Public')}
										</span>
									</Tooltip>
								{/if}
								{#if agent.is_featured}
									<Tooltip content={$i18n.t('Featured by admin')}>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											viewBox="0 0 24 24"
											fill="currentColor"
											class="size-3 text-amber-500 shrink-0"
										>
											<path
												fill-rule="evenodd"
												d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.006 5.404.434c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.434 2.082-5.006Z"
												clip-rule="evenodd"
											/>
										</svg>
									</Tooltip>
								{/if}
							</div>

							<!-- Actions — shown for all; locked agents get the modal instead of install -->
							<div class="flex items-center gap-1 shrink-0">
								<Tooltip content={accessible ? $i18n.t('Install') : $i18n.t('Access restricted')}>
									<button
										class="p-1.5 rounded-lg transition
											{accessible
												? 'hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300'
												: 'text-gray-400 dark:text-gray-600 cursor-not-allowed'}"
										on:click={() => handleInstall(agent)}
									>
										<ArrowDownTray className="size-4" />
									</button>
								</Tooltip>

								{#if isOwnerOrAdmin(agent)}
									<!-- Public / Private toggle -->
									<Tooltip
										content={isPublic(agent)
											? $i18n.t('Make Private')
											: $i18n.t('Make Public — visible to all users')}
									>
										<button
											class="p-1.5 rounded-lg transition {isPublic(agent)
												? 'hover:bg-green-100 dark:hover:bg-green-900/30 text-green-600 dark:text-green-400'
												: 'hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-400 dark:text-gray-500'}"
											on:click={() => handleTogglePublic(agent)}
										>
											{#if isPublic(agent)}
												<!-- Globe (public) -->
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
														d="M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 0 1 3 12c0-1.605.42-3.113 1.157-4.418"
													/>
												</svg>
											{:else}
												<!-- Lock (private) -->
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
														d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z"
													/>
												</svg>
											{/if}
										</button>
									</Tooltip>

									<!-- Feature toggle (admin only) -->
									{#if $user?.role === 'admin'}
										<Tooltip
											content={agent.is_featured
												? $i18n.t('Unfeature agent')
												: $i18n.t('Feature agent')}
										>
											<button
												class="p-1.5 rounded-lg transition {agent.is_featured
													? 'hover:bg-amber-100 dark:hover:bg-amber-900/30 text-amber-500'
													: 'hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-400 dark:text-gray-500'}"
												on:click={() => handleToggleFeatured(agent)}
											>
												<svg
													xmlns="http://www.w3.org/2000/svg"
													viewBox="0 0 24 24"
													fill={agent.is_featured ? 'currentColor' : 'none'}
													stroke={agent.is_featured ? 'none' : 'currentColor'}
													stroke-width="1.5"
													class="size-4"
												>
													<path
														fill-rule="evenodd"
														d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.006 5.404.434c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.434 2.082-5.006Z"
														clip-rule="evenodd"
													/>
												</svg>
											</button>
										</Tooltip>
									{/if}

									<Tooltip content={$i18n.t('Delete')}>
										<button
											class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 transition"
											on:click={() => handleDelete(agent)}
										>
											<GarbageBin className="size-4" />
										</button>
									</Tooltip>
								{/if}
							</div>
						</div>

						<div
							class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mt-1"
							title={agent.description ?? ''}
						>
							{agent.description || $i18n.t('No description')}
						</div>

						<div class="mt-2 flex flex-wrap gap-1">
							<!-- Trust shield badge -->
							<TrustShieldBadge
								tier={agent.trust_tier ?? 'public'}
								locked={!accessible}
							/>

							{#if agent.foundational_model}
								<span
									class="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
								>
									{agent.foundational_model}
								</span>
							{/if}
							{#if agent.tools?.capabilities}
								{#each Object.keys(agent.tools.capabilities) as cap}
									<span
										class="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
									>
										{cap}
									</span>
								{/each}
							{/if}
						</div>
					</div>
				</div>

				<div
					class="mt-2 pt-2 border-t border-gray-100 dark:border-gray-800 flex justify-between items-center text-xs text-gray-500"
				>
					<div class="truncate max-w-[200px]" title={agent.url}>{agent.url}</div>
				</div>
			</div>
		{/each}
	</div>
{:else}
	<div class="w-full h-full flex justify-center items-center">
		<Spinner />
	</div>
{/if}
