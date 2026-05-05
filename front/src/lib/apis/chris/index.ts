import { WEBUI_API_BASE_URL } from '$lib/constants';

// ─── Types ────────────────────────────────────────────────────────────────────

export type HistoryMessage = {
	role: string;
	content: string;
};

export type ChrisMessageResponse = {
	routed_to: string | null;
	agent_name: string | null;
	response: string;
};

export type SuggestionItem = {
	id: string;
	name: string;
	description: string | null;
	image_url: string | null;
	url: string;
};

// ─── API calls ────────────────────────────────────────────────────────────────

/**
 * Send a message to Chris. Chris will either route it to an installed agent
 * or answer directly via Gemini.
 */
export const sendChrisMessage = async (
	token: string,
	payload: {
		message: string;
		chat_id?: string;
		history?: HistoryMessage[];
	}
): Promise<ChrisMessageResponse | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chris/message`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			message: payload.message,
			chat_id: payload.chat_id ?? '',
			history: payload.history ?? []
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error('sendChrisMessage error:', err);
			return null;
		});

	if (error) {
		throw error;
	}
	return res;
};

/**
 * Get marketplace agent suggestions relevant to a query string.
 * Returns agents the user has NOT yet installed.
 */
export const getChrisSuggestions = async (
	token: string,
	q: string,
	limit = 3
): Promise<SuggestionItem[]> => {
	const params = new URLSearchParams({ q, limit: String(limit) });

	const res = await fetch(`${WEBUI_API_BASE_URL}/chris/suggestions?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error('getChrisSuggestions error:', err);
			return [];
		});

	return res ?? [];
};

/**
 * Register a marketplace agent by its A2A URL (used by suggestion chip "Add" button).
 */
export const installAgentByUrl = async (
	token: string,
	agentUrl: string
): Promise<boolean> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/register-by-url`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ agent_url: agentUrl })
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error('installAgentByUrl error:', err);
			return null;
		});

	return res !== null;
};
