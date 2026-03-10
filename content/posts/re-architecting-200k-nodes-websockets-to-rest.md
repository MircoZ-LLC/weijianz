---
title: "Re-Architecting for 200k Nodes: Why We Trashed WebSockets for Stateless REST"
date: 2026-03-09
draft: false
tags: ['AWS', 'ECS', 'Distributed Systems', 'Architecture', 'Observability']
description: 'How we scaled an ECS observability service from a stateful WebSocket nightmare to a 200k-node, 10k RPS stateless REST architecture.'
showTableOfContents: true
---

As a Lead Engineer, you often face a choice: use the "coolest" tech or use the tech that actually scales.

When my team and I took over the ECS Managed Instance Observability Service, we were staring down a massive scaling challenge. We needed to support over 200,000 managed instances sending telemetry every 20 seconds. Our legacy system was buckling at just a fraction of that load.

Here is the story of how we moved from a stateful nightmare to a high-performance stateless architecture.

## The "Stateful" Wall: 100 Connections per Node

The original system used WebSockets. In theory, WebSockets are great for real-time data. In practice, at our scale, they were a disaster for two reasons:

**The Memory Ceiling:** Each agent held a persistent, "pinned" connection. Our backend nodes were limited to roughly 100 active connections each because they were stuck in a synchronous, thread-per-connection model.

**The 65k Port Limit:** Even if we beefed up the servers, we hit a physical wall at the Proxy/Load Balancer layer. A single IP address on an AWS Load Balancer can only handle 65,535 source ports. With 200k agents trying to stay "connected" for 15 minutes at a time, we were guaranteed to exhaust the port pool, leading to massive connection drops.

## The Pivot: Choosing REST and Async I/O

We made a controversial but necessary call: Move to Stateless REST. Many engineers argue for gRPC or WebSockets for "efficiency," but for an agent that only sends data every 20 seconds, the overhead of a REST call is negligible compared to the massive cost of maintaining 200,000 idle connections.

**The Architecture Shift:**

- **From Stateful to Request-Response:** By switching to REST, we freed up the Load Balancer ports immediately after the 200ms data transfer.
- **Async I/O Model:** We implemented an asynchronous request-handling loop. Instead of one thread waiting on one agent, a single thread could now manage thousands of incoming telemetry packets.

Result: We boosted single-node concurrency by **10x**.

## Security & Privacy at Scale

Scaling isn't just about throughput; it's about trust. We implemented two critical layers:

**VPC Path Validation:** We didn't just trust the agent's token. We added a layer that verified the request was coming from a valid internal VPC path. This prevented "Identity Injection" attacks where a leaked token could be used to spoof data from outside the network.

**Masking at the Edge:** Using OpenTelemetry (OTel) agents, we pushed data masking to the source. Sensitive customer data is scrubbed on the instance before it ever hits our ingestors. This reduced our compliance surface area and saved us from processing "junk" data in the cloud.

## The Impact

By the end of the first year, the numbers spoke for themselves:

- **Fleet Size:** Successfully managed 200,000+ instances.
- **Throughput:** Stabilized at 10,000 Requests Per Second (RPS).
- **Operational Excellence:** By centralizing monitoring via CloudWatch cross-account dashboards, we cut our on-call response time by **80%**.

## The Lesson

In distributed systems, **state is the enemy of scale**. By moving the "state" out of the network layer and back to the application logic, we transformed a fragile service into a robust, AWS-scale observability engine.
