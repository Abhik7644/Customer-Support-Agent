import { useState } from "react";
import Login from "./Login";
import Chat from "./Chat";
import AgentProfile from "./AgentProfile";
import { getAuthToken, logout } from "./api";
import "./App.css";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(!!getAuthToken());

  function handleLogout() {
    logout();
    setLoggedIn(false);
  }

  return (
    <div className="app">
      <div className="header">
        <div className="brand">
          <h1>ShopEase</h1>
        </div>
        {loggedIn && (
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div className="status-pill">
              <span className="status-dot" />
              Support online
            </div>
            <button className="logout-button" onClick={handleLogout}>
              Log out
            </button>
          </div>
        )}
      </div>
      {loggedIn ? (
        <div className="app-layout">
          <AgentProfile/>
          <Chat /> 
        </div>
      ): ( 
      <Login onLoggedIn={() => setLoggedIn(true)} />
      )}
    </div>
  );
}