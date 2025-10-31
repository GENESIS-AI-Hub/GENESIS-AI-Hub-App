import React, { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [agents, setAgents] = useState([]);
  const [chats, setChats] = useState([]);
  const [activeChat, setActiveChat] = useState(null);
  const [activeChatMessages, setActiveChatMessages] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [newChatTitle, setNewChatTitle] = useState("");
  const [showAgentRegistration, setShowAgentRegistration] = useState(false);
  const [agentRegistrationUrl, setAgentRegistrationUrl] = useState("");
  const [agentRegistrationStatus, setAgentRegistrationStatus] = useState("");
  const messagesEndRef = useRef(null);

  // Backend API base URL
  const BACKEND_URL =
    process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

  // Fetch agents from backend
  useEffect(() => {
    fetchAgents();
  }, []);

  // Fetch chats from backend
  useEffect(() => {
    fetchChats();
  }, []);

  // Fetch messages when active chat changes
  useEffect(() => {
    if (activeChat) {
      fetchMessages(activeChat.id);
    } else {
      setActiveChatMessages([]);
    }
  }, [activeChat]);

  // Scroll to bottom of messages
  useEffect(() => {
    scrollToBottom();
  }, [activeChatMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchAgents = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/agents`);
      const data = await response.json();
      setAgents(data);
      if (data.length > 0 && !selectedAgent) {
        setSelectedAgent(data[0].id);
      }
    } catch (error) {
      console.error("Error fetching agents:", error);
    }
  };

  const fetchChats = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/chats`);
      const data = await response.json();
      setChats(data);
    } catch (error) {
      console.error("Error fetching chats:", error);
    }
  };

  const fetchMessages = async (chatId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/chats/${chatId}/messages`);
      const data = await response.json();
      setActiveChatMessages(data);
    } catch (error) {
      console.error("Error fetching messages:", error);
    }
  };

  const createNewChat = async () => {
    if (!selectedAgent || !newChatTitle.trim()) {
      alert("Please select an agent and enter a chat title");
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/chats`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: newChatTitle,
          agent_id: selectedAgent,
        }),
      });

      if (response.ok) {
        const newChat = await response.json();
        setChats([...chats, newChat]);
        setActiveChat(newChat);
        setNewChatTitle("");
      } else {
        throw new Error("Failed to create chat");
      }
    } catch (error) {
      console.error("Error creating chat:", error);
      alert("Error creating chat: " + error.message);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !activeChat) return;

    const messageToSend = inputMessage.trim();
    setInputMessage("");

    // Add user message optimistically
    const newUserMessage = {
      id: "temp-user-" + Date.now(),
      role: "user",
      content: messageToSend,
      timestamp: new Date().toISOString(),
    };

    setActiveChatMessages((prev) => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(
        `${BACKEND_URL}/chats/${activeChat.id}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            content: messageToSend,
          }),
        }
      );

      if (response.ok) {
        const assistantMessage = await response.json();
        // Replace the temporary user message and add the assistant response
        setActiveChatMessages((prev) => {
          const filtered = prev.filter(
            (msg) => !msg.id.startsWith("temp-user-")
          );
          return [...filtered, newUserMessage, assistantMessage];
        });
      } else {
        throw new Error("Failed to send message");
      }
    } catch (error) {
      console.error("Error sending message:", error);
      // Remove the temporary message and show error
      setActiveChatMessages((prev) =>
        prev.filter((msg) => msg.id !== newUserMessage.id)
      );
      alert("Error sending message: " + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleNewChat = () => {
    setNewChatTitle("");
    setSelectedAgent(selectedAgent || (agents.length > 0 ? agents[0].id : ""));
    setActiveChat(null);
  };

  const selectChat = (chat) => {
    setActiveChat(chat);
  };

  const getAgentName = (agentId) => {
    const agent = agents.find((a) => a.id === agentId);
    return agent ? agent.name : agentId;
  };

  const registerAgentByUrl = async () => {
    if (!agentRegistrationUrl.trim()) {
      setAgentRegistrationStatus("Please enter an agent URL");
      return;
    }

    setAgentRegistrationStatus("Registering agent...");
    try {
      const response = await fetch(`${BACKEND_URL}/agents/register-by-url`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ agent_url: agentRegistrationUrl.trim() }),
      });

      if (response.ok) {
        const registeredAgent = await response.json();
        setAgentRegistrationStatus(
          `Successfully registered agent: ${registeredAgent.name}`
        );
        // Refresh the agents list
        fetchAgents();
        // Clear the input
        setAgentRegistrationUrl("");
        setTimeout(() => {
          setAgentRegistrationStatus("");
          setShowAgentRegistration(false);
        }, 3000);
      } else {
        const errorData = await response.json();
        setAgentRegistrationStatus(
          `Error: ${errorData.detail || "Failed to register agent"}`
        );
      }
    } catch (error) {
      setAgentRegistrationStatus(`Error: ${error.message}`);
    }
  };

  const handleTestWellKnown = async () => {
    if (!agentRegistrationUrl.trim()) {
      setAgentRegistrationStatus("Please enter an agent URL");
      return;
    }

    setAgentRegistrationStatus("Testing .well-known file...");
    try {
      const response = await fetch(
        `${BACKEND_URL}/agents/fetch-well-known?agent_url=${encodeURIComponent(
          agentRegistrationUrl.trim()
        )}`
      );

      if (response.ok) {
        const agentData = await response.json();
        setAgentRegistrationStatus(
          `Found agent: ${agentData.name} - ${agentData.description}`
        );
      } else {
        const errorData = await response.json();
        setAgentRegistrationStatus(
          `Error: ${errorData.detail || "Failed to fetch .well-known file"}`
        );
      }
    } catch (error) {
      setAgentRegistrationStatus(`Error: ${error.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-blue-900">OSU Genesis Hub</h1>
        </div>

        <div className="p-4 space-y-2">
          <button
            onClick={handleNewChat}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
          >
            + New Chat
          </button>
          <button
            onClick={() => setShowAgentRegistration(true)}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
          >
            + Register Agent
          </button>
        </div>

        {/* Agent Registration Modal */}
        {showAgentRegistration && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">
                    Register New Agent
                  </h3>
                  <button
                    onClick={() => {
                      setShowAgentRegistration(false);
                      setAgentRegistrationStatus("");
                    }}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Agent URL (with .well-known/a2a-agent)
                  </label>
                  <input
                    type="text"
                    value={agentRegistrationUrl}
                    onChange={(e) => setAgentRegistrationUrl(e.target.value)}
                    placeholder="https://agent-domain.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex space-x-2 mb-4">
                  <button
                    onClick={handleTestWellKnown}
                    className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
                  >
                    Test .well-known
                  </button>
                  <button
                    onClick={registerAgentByUrl}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
                  >
                    Register
                  </button>
                </div>

                {agentRegistrationStatus && (
                  <div
                    className={`text-sm p-2 rounded ${
                      agentRegistrationStatus.startsWith("Error")
                        ? "bg-red-100 text-red-700"
                        : agentRegistrationStatus.includes("Successfully")
                        ? "bg-green-100 text-green-700"
                        : "bg-blue-100 text-blue-700"
                    }`}
                  >
                    {agentRegistrationStatus}
                  </div>
                )}

                <div className="mt-4 text-xs text-gray-500">
                  The agent must have a .well-known/agent.json endpoint that
                  returns agent information in JSON format.
                  <br />
                  Example:
                  https://hello-world-gxfr.onrender.com/.well-known/agent.json
                </div>
              </div>
            </div>
          </div>
        )}

        {/* New Chat Form */}
        {(!activeChat || newChatTitle) && (
          <div className="p-4 border-t border-gray-200">
            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Chat Title
              </label>
              <input
                type="text"
                value={newChatTitle}
                onChange={(e) => setNewChatTitle(e.target.value)}
                placeholder="Enter chat title..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Agent
              </label>
              <select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={createNewChat}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
            >
              Start Chat
            </button>
          </div>
        )}

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-2">
          <h3 className="text-sm font-medium text-gray-500 px-2 mb-2">
            Recent Chats
          </h3>
          <ul className="space-y-1">
            {chats.map((chat) => (
              <li key={chat.id}>
                <button
                  onClick={() => selectChat(chat)}
                  className={`w-full text-left p-2 rounded-md text-sm ${
                    activeChat && activeChat.id === chat.id
                      ? "bg-blue-100 text-blue-800"
                      : "hover:bg-gray-100 text-gray-700"
                  }`}
                >
                  <div className="font-medium truncate">{chat.title}</div>
                  <div className="text-xs text-gray-500">
                    {getAgentName(chat.agent_id)}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        {activeChat && (
          <div className="bg-white border-b border-gray-200 p-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-800">
                {activeChat.title}
              </h2>
              <p className="text-sm text-gray-500">
                Agent: {getAgentName(activeChat.agent_id)}
              </p>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 bg-gradient-to-b from-gray-50 to-gray-100">
          {activeChat ? (
            <div className="max-w-3xl mx-auto space-y-6">
              {activeChatMessages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-xl p-4 ${
                      message.role === "user"
                        ? "bg-blue-500 text-white rounded-tr-none"
                        : "bg-white text-gray-800 rounded-tl-none border border-gray-200"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    <div
                      className={`text-xs mt-1 ${
                        message.role === "user"
                          ? "text-blue-100"
                          : "text-gray-500"
                      }`}
                    >
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="max-w-[80%] bg-white text-gray-800 rounded-xl rounded-tl-none border border-gray-200 p-4">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></div>
                      <div
                        className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      ></div>
                      <div
                        className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
                        style={{ animationDelay: "0.4s" }}
                      ></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <h3 className="text-xl font-medium text-gray-600 mb-2">
                  Welcome to OSU Genesis Hub
                </h3>
                <p className="text-gray-500 mb-4">
                  Select an existing chat or create a new one to start
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        {activeChat && (
          <div className="bg-white border-t border-gray-200 p-4">
            <div className="max-w-3xl mx-auto">
              <div className="flex space-x-3">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Type your message..."
                  className="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows="1"
                  style={{ minHeight: "48px", maxHeight: "120px" }}
                />
                <button
                  onClick={sendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className={`px-4 py-2 rounded-lg font-medium ${
                    isLoading || !inputMessage.trim()
                      ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                      : "bg-blue-600 hover:bg-blue-700 text-white"
                  }`}
                >
                  Send
                </button>
              </div>
              <div className="mt-2 text-xs text-gray-500 text-center">
                Press Enter to send, Shift+Enter for new line
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
