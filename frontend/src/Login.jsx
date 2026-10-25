import { useState } from "react";
import { login, register, setAuthToken } from "./api";

export default function Login({ onLoggedIn }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const token = isRegistering
        ? await register(name, email, password)
        : await login(email, password);
      setAuthToken(token);
      onLoggedIn();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Something went wrong. Please try again."
      );
    }
  }

  return (
    <div className="login-container">
      <h2>{isRegistering ? "Create an account" : "Log in"}</h2>
      <form onSubmit={handleSubmit}>
        {isRegistering && (
          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        )}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p className="error">{error}</p>}
        <button type="submit">{isRegistering ? "Register" : "Log in"}</button>
      </form>
      <button className="link-button" onClick={() => setIsRegistering(!isRegistering)}>
        {isRegistering ? "Already have an account? Log in" : "New here? Register"}
      </button>
    </div>
  );
}