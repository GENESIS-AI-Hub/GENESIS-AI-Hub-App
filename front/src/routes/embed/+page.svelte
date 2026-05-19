<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { getBackendConfig } from '$lib/apis';
	import { getSessionUser } from '$lib/apis/auths';

	let agentId = '';
	let agent = null;
	let availableAgents = [];
	let messages = [];
	let input = '';
	let loading = false;
	let chatElement;
	let showSelector = true;

	// Auth state
	let authenticated = false;
	let authChecked = false;
	let oauthProviders: Record<string, string> = {};

	const scrollToBottom = async () => {
		await tick();
		if (chatElement) {
			chatElement.scrollTop = chatElement.scrollHeight;
		}
	};

	const openOAuthPopup = (provider: string) => {
		const url = `${WEBUI_BASE_URL}/oauth/${provider}/login?popup=1`;
		window.open(url, 'oauth_popup', 'width=500,height=650,noopener=0');
	};

	const handlePopupMessage = async (event: MessageEvent) => {
		// Only accept messages from same origin
		if (event.origin !== window.location.origin) return;
		if (!event.data || event.data.type !== 'oauth_complete') return;

		const { token } = event.data;
		if (!token) return;

		try {
			const sessionUser = await getSessionUser(token);
			if (sessionUser) {
				localStorage.token = token;
				authenticated = true;
				loadAgents();
			}
		} catch {
			toast.error('Sign in failed. Please try again.');
		}
	};

	const loadAgents = async () => {
		try {
			const res = await fetch('/api/embed/agents');
			if (res.ok) {
				availableAgents = await res.json();
			} else {
				toast.error('Failed to load agents');
			}
		} catch (e) {
			console.error(e);
			toast.error('Error loading agents');
		}
	};

	// Load agents list on mount
	onMount(async () => {
		window.addEventListener('message', handlePopupMessage);

		// Check for existing session
		const token = localStorage.token;
		if (token) {
			try {
				const sessionUser = await getSessionUser(token);
				if (sessionUser) {
					authenticated = true;
				}
			} catch {
				// Token expired or invalid; fall through to sign-in UI
				delete localStorage.token;
			}
		}

		authChecked = true;

		if (authenticated) {
			await loadAgents();
		} else {
			// Fetch provider list so we can render sign-in buttons
			try {
				const backendConfig = await getBackendConfig();
				oauthProviders = backendConfig?.oauth?.providers ?? {};
			} catch {
				// No providers available
			}
		}
	});

	onDestroy(() => {
		window.removeEventListener('message', handlePopupMessage);
	});

	// Reactive logic to load agent when URL changes
	$: {
		const newAgentId = $page.url.searchParams.get('agent_id') || '';
		
		if (newAgentId !== agentId) {
			agentId = newAgentId;
			
			if (agentId) {
				showSelector = false;
				agent = null; // Reset agent
				
				// Load local history
				const saved = localStorage.getItem(`embed_chat_${agentId}`);
				if (saved) {
					try {
						messages = JSON.parse(saved);
					} catch (e) {
						console.error('Failed to parse saved chat', e);
						messages = [];
					}
				} else {
					messages = [];
				}
				
				// Fetch agent details
				(async () => {
					try {
						const res = await fetch(`/api/embed/agent/${agentId}`);
						if (res.ok) {
							agent = await res.json();
						} else {
							toast.error('Failed to load agent details');
						}
					} catch (e) {
						console.error(e);
						toast.error('Error loading agent');
					}
					scrollToBottom();
				})();
			} else {
				showSelector = true;
				agent = null;
				messages = [];
			}
		}
	}

	const selectAgent = (selectedAgentId) => {
		goto(`/embed/?agent_id=${selectedAgentId}`);
	};

	const saveChat = () => {
		if (agentId) {
			localStorage.setItem(`embed_chat_${agentId}`, JSON.stringify(messages));
		}
	};

	const submitMessage = async () => {
		if (!input.trim() || loading) return;

		const userMsg = { role: 'user', content: input };
		messages = [...messages, userMsg];
		input = '';
		loading = true;
		saveChat();
		scrollToBottom();

		try {
			const res = await fetch('/api/embed/chat/completions', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					model: agentId,
					messages: messages,
					stream: true
				})
			});

			if (!res.ok) {
				const err = await res.json();
				throw new Error(err.detail || 'Failed to send message');
			}

			// Handle streaming
			const reader = res.body.getReader();
			const decoder = new TextDecoder();
			let assistantMsg = { role: 'assistant', content: '' };
			messages = [...messages, assistantMsg];

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const chunk = decoder.decode(value);
				const lines = chunk.split('\n');
				
                for (const line of lines) {
					if (line.startsWith('data: ')) {
						const dataStr = line.slice(6);
						if (dataStr === '[DONE]') break;
						
                        try {
							const data = JSON.parse(dataStr);
							const delta = data.choices?.[0]?.delta?.content || '';
							assistantMsg.content += delta;
							messages = [...messages.slice(0, -1), assistantMsg];
                            scrollToBottom();
						} catch (e) {
							// ignore parse errors for partial chunks
						}
					}
				}
			}
            saveChat();

		} catch (e) {
			toast.error(e.message);
            messages = [...messages, { role: 'system', content: `Error: ${e.message}` }];
		} finally {
			loading = false;
            saveChat();
		}
	};
    
    const handleKeydown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitMessage();
        }
    }
</script>

{#if !authChecked}
	<!-- Waiting for auth check -->
	<div class="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
		<div class="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
	</div>
{:else if !authenticated}
	<!-- Sign-in wall -->
	<div class="flex flex-col h-screen items-center justify-center bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100 gap-6 px-8">
		<img src="/favicon.png" alt="logo" class="w-12 h-12 rounded-full" />
		<div class="text-center">
			<h1 class="text-xl font-semibold">Sign in to continue</h1>
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Authentication required to use this chat</p>
		</div>
		<div class="flex flex-col gap-2 w-full max-w-xs">
			{#if oauthProviders.google}
				<button
					on:click={() => openOAuthPopup('google')}
					class="flex justify-center items-center gap-3 w-full rounded-full py-2.5 text-sm font-medium bg-gray-700/5 hover:bg-gray-700/10 dark:bg-gray-100/5 dark:hover:bg-gray-100/10 dark:text-gray-300 transition"
				>
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" class="size-5">
						<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/><path fill="none" d="M0 0h48v48H0z"/>
					</svg>
					Continue with Google
				</button>
			{/if}
			{#if oauthProviders.microsoft}
				<button
					on:click={() => openOAuthPopup('microsoft')}
					class="flex justify-center items-center gap-3 w-full rounded-full py-2.5 text-sm font-medium bg-gray-700/5 hover:bg-gray-700/10 dark:bg-gray-100/5 dark:hover:bg-gray-100/10 dark:text-gray-300 transition"
				>
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 21 21" class="size-5">
						<rect x="1" y="1" width="9" height="9" fill="#f25022"/><rect x="1" y="11" width="9" height="9" fill="#00a4ef"/><rect x="11" y="1" width="9" height="9" fill="#7fba00"/><rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
					</svg>
					Continue with Microsoft
				</button>
			{/if}
			{#if oauthProviders.github}
				<button
					on:click={() => openOAuthPopup('github')}
					class="flex justify-center items-center gap-3 w-full rounded-full py-2.5 text-sm font-medium bg-gray-700/5 hover:bg-gray-700/10 dark:bg-gray-100/5 dark:hover:bg-gray-100/10 dark:text-gray-300 transition"
				>
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="size-5">
						<path fill="currentColor" d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.92 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57C20.565 21.795 24 17.31 24 12c0-6.63-5.37-12-12-12z"/>
					</svg>
					Continue with GitHub
				</button>
			{/if}
			{#if oauthProviders.oidc}
				<button
					on:click={() => openOAuthPopup('oidc')}
					class="flex justify-center items-center gap-3 w-full rounded-full py-2.5 text-sm font-medium bg-gray-700/5 hover:bg-gray-700/10 dark:bg-gray-100/5 dark:hover:bg-gray-100/10 dark:text-gray-300 transition"
				>
					Continue with SSO
				</button>
			{/if}
			{#if Object.keys(oauthProviders).length === 0}
				<p class="text-sm text-center text-gray-400">No sign-in providers are configured.</p>
			{/if}
		</div>
	</div>
{:else if showSelector}
	<!-- Agent Selection View -->
	<div class="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100">
		<div class="px-6 py-4 border-b dark:border-gray-800 bg-white dark:bg-gray-950">
			<h1 class="text-xl font-semibold">Select an Agent</h1>
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Choose an agent to start chatting</p>
		</div>

		<div class="flex-1 overflow-y-auto p-6">
			{#if availableAgents.length === 0}
				<div class="flex items-center justify-center h-full">
					<div class="text-center">
						<div class="w-12 h-12 rounded-full bg-gray-200 dark:bg-gray-800 animate-pulse mx-auto mb-4"></div>
						<p class="text-gray-400">Loading agents...</p>
					</div>
				</div>
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-6xl mx-auto">
					{#each availableAgents as agentOption}
						<button
							on:click={() => selectAgent(agentOption.id)}
							class="p-5 border dark:border-gray-700 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition text-left group"
						>
							<div class="flex items-start gap-3">
								<img
									src={agentOption.profile_image_url || '/favicon.png'}
									alt={agentOption.name}
									class="w-12 h-12 rounded-full object-cover flex-shrink-0"
								/>
								<div class="flex-1 min-w-0">
									<h3 class="font-semibold text-base group-hover:text-blue-600 dark:group-hover:text-blue-400 transition truncate">
										{agentOption.name}
									</h3>
									<p class="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
										{agentOption.description}
									</p>
								</div>
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{:else}
	<!-- Chat View -->
	<div class="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100 font-primary">
		<!-- Header -->
		<div class="px-4 py-3 border-b dark:border-gray-800 flex items-center gap-3 bg-white dark:bg-gray-950">
			<button
				on:click={() => goto('/embed/')}
				class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
				title="Back to agent selection"
			>
				<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
			</button>
			{#if agent}
				<img
					src={agent.profile_image_url || '/favicon.png'}
					alt={agent.name}
					class="w-8 h-8 rounded-full object-cover"
				/>
				<div>
					<h1 class="font-semibold text-sm">{agent.name}</h1>
					<p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1">{agent.description}</p>
				</div>
			{:else}
				<div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-800 animate-pulse"></div>
				<div class="flex-1">
					<div class="h-4 w-24 bg-gray-200 dark:bg-gray-800 rounded animate-pulse mb-1"></div>
					<div class="h-3 w-48 bg-gray-200 dark:bg-gray-800 rounded animate-pulse"></div>
				</div>
			{/if}
		</div>

		<!-- Chat Area -->
		<div class="flex-1 overflow-y-auto p-4 space-y-4" bind:this={chatElement}>
			{#if messages.length === 0}
				<div class="h-full flex flex-col items-center justify-center text-gray-400">
					<p>Start a conversation with {agent ? agent.name : 'the agent'}</p>
				</div>
			{/if}
			
			{#each messages as msg}
				<div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
					<div
						class="max-w-[85%] rounded-2xl px-4 py-2 {msg.role === 'user'
							? 'bg-blue-600 text-white rounded-br-none'
							: 'bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-bl-none'}"
					>
						<div class="whitespace-pre-wrap break-words text-sm">{msg.content}</div>
					</div>
				</div>
			{/each}
			
			{#if loading && messages[messages.length-1]?.role === 'user'}
				<div class="flex justify-start">
					<div class="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-2xl rounded-bl-none px-4 py-2">
						<div class="flex gap-1">
							<span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></span>
							<span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-100"></span>
							<span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-200"></span>
						</div>
					</div>
				</div>
			{/if}
		</div>

		<!-- Input Area -->
		<div class="p-4 border-t dark:border-gray-800 bg-white dark:bg-gray-950">
			<div class="relative flex items-end gap-2 bg-gray-100 dark:bg-gray-850 rounded-xl border dark:border-gray-800 p-2">
				<textarea
					bind:value={input}
					on:keydown={handleKeydown}
					placeholder="Message..."
					class="w-full bg-transparent border-none focus:ring-0 resize-none max-h-32 min-h-[24px] py-1 text-sm outline-none"
					rows="1"
				></textarea>
				<button
					on:click={submitMessage}
					disabled={!input.trim() || loading}
					class="p-1.5 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-700 transition"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="lucide lucide-arrow-up"
						><path d="m5 12 7-7 7 7" /><path d="M12 19V5" /></svg
					>
				</button>
			</div>
		</div>
	</div>
{/if}
