import rhinoscriptsyntax as rs

# -------------------------------
# Retrieve agents from upstream Grasshopper component
# -------------------------------

# `x` is the upstream component instance (from agent_builder)
agents = x.agents if x and hasattr(x, "agents") else []


# -------------------------------
# Step simulation
# -------------------------------

new_agents = []

for agent in agents:
    spawned = agent.update(agents, start_surface)

    if spawned:
        new_agents.append(spawned)

agents = agents + new_agents  # combine active agents and any new spawned ones


# -------------------------------
# Visualization outputs
# -------------------------------

P = []       # positions
V = []       # velocity vectors
Paths = []   # trails / paths

for agent in agents:
    # Position
    P.append(agent.position)

    # velocity as line
    try:
        end = rs.PointAdd(agent.position, agent.velocity)
        V.append(rs.AddLine(agent.position, end))
    except Exception:
        V.append(None)

    # Path history
    if agent.path:
        Paths.append(agent.path)


# -------------------------------
# Grasshopper Outputs
# -------------------------------

out_agents = agents
out_points = P
out_vectors = V
out_paths = Paths

print("Simulator running, total agents:", len(agents))