export default function AgentProfile() {
  return (
    <div className="agent-panel">
      <div className="agent-avatar">I</div>
      <div>
        <p className="agent-name">Ivy</p>
        <p className="agent-role">Support agent</p>
      </div>
      <ul className="agent-capabilities">
        <li>Order status &amp; tracking</li>
        <li>Refunds &amp; eligibility</li>
        <li>Return &amp; shipping policy</li>
        <li>Support tickets</li>
      </ul>
      <p className="trust-note">
        <strong>Refunds over ₹5,000</strong> are reviewed by a person before processing.
      </p>
    </div>
  );
}