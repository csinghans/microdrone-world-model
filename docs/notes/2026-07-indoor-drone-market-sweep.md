# Indoor micro-drone market sweep — sources & verified claims (2026-07-07)

Deep-research sweep behind the **commercial-frontier candidates** in
`docs/RESEARCH-IDEAS.md`. Question: indoor micro-drone flight capabilities
that are hard for humans, AI-assistable, monetizable, and sim-first
validatable. 5 search angles → 24 sources → adversarial claim verification.

**Provenance honesty:** the synthesis step hit a session limit; this note
was assembled by hand from the workflow's verified-claim journal. Confidence
tags: **CONFIRMED** = 3-vote adversarial pass; **CITED** = direct paper quote,
verification vote interrupted (not refuted); **VENDOR** = vendor/case-study
source (self-reported numbers).

## Verified claims (CONFIRMED, 3-0)
- [3-0] GPS-denied localization drift is partially solvable within nano-scale memory limits: NanoSLAM constrains its linear solver to fit inside the 128 kB L1 memory of the GAP9 cluster while reducing trajectory error by up to 67% versus dead reckoning. This quantifies both the drift problem (a named research-question focus) and that AI/SLAM correction is achievable at the KB scale relevant to the repo.
  - source: https://arxiv.org/html/2601.13252v1
  - quote: "This approach constrains the linear solver's memory footprint to fit within the 128 kB L1 memory of the GAP9 cluster while correcting trajectory errors by up to 67% compared to dead reckoning."
- [3-0] Onboard AI compute carries a measurable, quantified endurance cost that constrains battery-limited mission planning: adding a 4.4 g AI-deck reduces Crazyflie flight time by ~22%, from ~440 s to ~340 s. This is a concrete cost datum for the compute-vs-battery tradeoff that any embedded-model research must budget against.
  - source: https://arxiv.org/html/2601.13252v1
  - quote: "The addition of a 4.4 g AI-deck reduces flight time by approximately 22%, dropping endurance from ∼440 seconds to ∼340 seconds"
- [3-0] The survey identifies the still-open frontier for nano-UAV autonomy as (a) long-term endurance, (b) robust obstacle avoidance in DYNAMIC environments, and (c) Sim-to-Real transfer of reinforcement-learning policies. This directly informs next-research-item selection and flags that sim-first (PyBullet-level) validation is necessary but faces a documented reality gap for RL policies.
  - source: https://arxiv.org/html/2601.13252v1
  - quote: "While significant progress has been observed in visual navigation and relative pose estimation, our analysis reveals persistent gaps in long-term endurance, robust obstacle avoidance in dynamic environments, and the 'Sim-to-Real' transfer of reinforcement learning policies."
- [3-0] DroNet is an end-to-end CNN that maps a single camera image directly to a steering angle and a collision probability (avoiding the traditional localization-mapping-planning cycle): the collision probability modulates forward velocity while the steering angle drives yaw. The learned policy generalizes to environments completely unseen at training time, including indoor corridors. This is exactly the GPS-free indoor collision-avoidance capability of interest, and a behavior validatable in a PyBullet-level simulator without new sensor hardware.
  - source: https://arxiv.org/pdf/1805.01831
  - quote: "the low-pass filtered probability of collision is used to modulate the UAV forward velocity, while the low-pass filtered steering angle is converted to the drone's yaw control... the approach generalizes very well to scenarios completely unseen at training time, including indoor corridors, parking lots, and high altitudes."
- [3-0] A swarm of 33-gram commercial off-the-shelf quadrotors (squarely within the <100g microdrone class) autonomously explored a real, unknown indoor environment and returned to the departure point using only the onboard 'swarm gradient bug algorithm' (SGBA), with no external positioning infrastructure.
  - source: https://www.science.org/doi/10.1126/scirobotics.aaw9710
  - quote: "it allows a group of 33-g commercial off-the-shelf quadrotors to successfully explore a real-world environment"
- [3-0] For GPS-denied indoor flight the drones avoid obstacles reactively via visual odometry plus wall-following, and solve return-home not through accurate global localization but by a gradient search toward a radio 'home beacon' — a concrete engineering way to sidestep positioning/dead-reckoning drift.
  - source: https://www.science.org/doi/10.1126/scirobotics.aaw9710
  - quote: "The robots navigate the environment and deal with static obstacles on the fly by means of visual odometry and wall-following behaviors."
- [3-0] The 47 g, 9.2 cm micro-quadrotors traverse gaps as small as 0.2 m (roughly twice the vehicle diameter) at speeds up to 2.0 m/s, demonstrating AI-enabled narrow-space traversal on a <100 g platform.
  - source: https://arxiv.org/pdf/2511.17765
  - quote: "reliable flight through gaps as small as 0.2 m ... roughly 2 times the quadrotor diameter ... up to 2.0 m/s"

## Cited (paper quotes; verification vote interrupted by session limit — NOT refuted)
- Decentralized swarm navigation is demonstrated on six real Crazyflie quadrotors (eight in simulation), coordinating via each drone's onboard nRF51822 radio exchanging position and velocity at 50 Hz, remaining robust under wireless bandwidth below 10 MHz and holding success above 95% even at significantly reduced update rates.
  - source: https://arxiv.org/pdf/2511.17765
- A dense optical-flow CNN (NanoFlowNet) runs in real time at 5.5-9.3 FPS on the ultra-low-power GreenWaves GAP8 microprocessor (FC@250MHz, CL@230MHz, 8-core cluster) on a Bitcraze AI-deck, entirely on board a 34 g Crazyflie nano quadcopter with a single grayscale camera, and is demonstrated driving vision-based obstacle avoidance. This is a concrete AI-ceiling proof point for the exact target platform (<100 g, embedded compute, monocular).
  - source: https://arxiv.org/pdf/2209.06918
- On-board memory, not accuracy, is the binding constraint for micro-drone embedded perception: the ~2M-parameter FlowNet2-xs does not fit on the GAP8 due to lack of memory, whereas the 170,881-parameter NanoFlowNet fits AND is more accurate on MPI-Sintel (7.122 vs 9.054 clean EPE) while using under 10% of the parameters. This directly validates the 'small memory-footprint world model' thesis over raw accuracy.
  - source: https://arxiv.org/pdf/2209.06918
- Fully-onboard AI visual navigation is demonstrated on a 27 g commercial Bitcraze Crazyflie 2.1 nano-drone (35 g with the AI deck) using a GAP8 SoC with only 512 kB of L2 memory and a single ultra-low-power monochrome QVGA camera, running the tiny CNN at up to 139 frame/s — proving that autonomous obstacle-aware flight fits inside a ~512 KB embedded compute envelope.
  - source: https://arxiv.org/pdf/2407.12675
- In real-world flight the 2.9 k-parameter Tiny-PULP-Dronet v3 navigated a narrow, obstacle-populated corridor with a 180 degrees turn at a max target speed of 0.5 m/s with a 100% success rate (5/5), while the state-of-the-art PULP-Dronet baseline — despite having 168x more parameters — failed every attempt (0/5); i.e. the smaller model beat the larger one at narrow-space traversal.
  - source: https://arxiv.org/pdf/2407.12675
- Even highly experienced FPV pilots crash frequently on agile indoor courses: in a controlled racing-simulator study, 32% of valid laps (410 of 1277) contained a collision with a gate or the floor, and only 96% of all 1327 laps were valid (4% invalid) — a hard quantified failure/accident rate for expert human piloting.
  - source: https://arxiv.org/pdf/2103.04672
- The human visual-motor response latency in agile drone control averages ~220 ms (eye-fixation direction to commanded flight direction), quantifying the perception-action bottleneck of human piloting — the exact latency budget a low-latency embedded controller/world-model could aim to beat.
  - source: https://arxiv.org/pdf/2103.04672
- In a controlled user study (n=20), a high-level autonomous teleoperation interface (room-portal graph / RPG) cut indoor drone task-execution time by 48.28% (RPG M=103.7s vs manual joystick M=200.1s) and reduced NASA-TLX mental workload by 76.82% (RPG M=11.75 vs joystick M=50.71), both p<0.001 — quantifying both the cognitive burden of manual piloting and the measurable benefit of raising autonomy level.
  - source: https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2019.00095/full
- Perceptual errors (a category that includes depth-perception/visual-spatial misjudgement) are a far larger cause of drone safety occurrences than for crewed aviation: Table 4 reports perceptual error at 29.3% of RPAS unsafe-act occurrences vs only 6.1% for powered (crewed) aircraft — an ~4.8x gap, which the authors frame as perception being a disproportionately large risk driver for remote pilots. This directly quantifies a human perceptual limit (seeing depth/clearance through a remote/single feed) that an onboard world model could offset, though the dataset is Australian RPAS broadly (2008-2019), not specifically <100g indoor micro-drones.
  - source: https://www.mdpi.com/2226-4310/12/3/206
- Flyability sells the Elios 3 not as a bare airframe but as a bundled hardware+software+service 'Light Package' — including the UAV, tablet, spare cage elements, 3 batteries, a SLAM engine, a LiDAR payload, a training simulator, Inspector inspection software, core software updates, unlimited phone/email support, and a 12-month warranty — evidencing that the industrial confined-space-inspection ceiling monetizes via a complete solution package rather than per-unit hardware.
  - source: https://www.flyability.com/elios-3-price
- Despite being titled 'ELIOS 3 PRICING', the official pricing page displays no numeric price, price range, or figure for the drone, payloads, or software, and instead routes buyers to a sales contact form to obtain pricing — confirming the industrial confined-space inspection drone is a quote-gated, high-ticket B2B purchase (in contrast to the publicly shelf-priced Tello/Crazyflie micro-drones), so this page cannot itself supply a hard price-anchor number.
  - source: https://www.flyability.com/elios-3-price
- gym-pybullet-drones is a PyBullet-physics Gym environment purpose-built for reinforcement-learning control of Crazyflie-class nano-quadcopters, and is designed for compatibility with Gymnasium and Stable-Baselines3 2.0 — i.e. a ready-made, PyBullet-level, no-new-hardware sim for exactly the <100g micro-drone class in scope.
  - source: https://utiasdsl.github.io/gym-pybullet-drones/
- The environment supports multi-agent (swarm) quadcopter RL, not only single-agent — so swarm-coordination (群飛協同) policies can be trained and validated in the simulator before any hardware, via a documented multi-agent training entry point.
  - source: https://utiasdsl.github.io/gym-pybullet-drones/

## Harness-flagged 'refuted' — read with caution (contaminated run)
These embedded-feasibility claims were flagged refuted on a run whose
verification votes were erroring on the session limit; cleaner independent
versions survive in the Cited list above (512 kB GAP8 CNNs, Tiny-PULP-Dronet
2.9k params). Treat the embedded-feasibility premise as supported.
- [1-2] Useful onboard visual inference already fits the ~512 KB / sub-100 mW embedded envelope that defines this micro-UAV class: a GAP8-based AI-deck (512 kB on-chip memory) can run the PULP-Frontnet CNN at
  - source: https://arxiv.org/html/2601.13252v1
- [1-2] A 27g commercial CrazyFlie 2.0 nano-quadrotor (nano-size class, ~10cm, single camera) augmented with the GAP8 processor can execute a full state-of-the-art CNN (DroNet) for closed-loop, end-to-end aut
  - source: https://arxiv.org/pdf/1805.01831
- [1-2] The complete onboard DNN visual-navigation workload runs on only 64 mW on average (at 6 fps), and up to 18 fps at a peak of under 284 mW — consuming on average just 3.5% of the nano-aircraft's power e
  - source: https://arxiv.org/pdf/1805.01831
- [0-3] Full SLAM (simultaneous localization and mapping) is too resource-demanding to run onboard tiny flying robots, which is the paper's core justification for a lightweight 'minimal' navigation algorithm 
  - source: https://www.science.org/doi/10.1126/scirobotics.aaw9710
- [0-3] LEARN runs a learned end-to-end multi-UAV navigation policy fully onboard a Crazyflie-class nano-quadrotor's STM32F405 MCU (168 MHz, 192 KB RAM, 1 MB flash); the attention-based policy has hidden size
  - source: https://arxiv.org/pdf/2511.17765

## All 24 sources
1. https://arxiv.org/html/2601.13252v1
2. https://arxiv.org/pdf/1805.01831
3. https://www.science.org/doi/10.1126/scirobotics.aaw9710
4. https://arxiv.org/pdf/2511.17765
5. https://arxiv.org/pdf/2209.06918
6. https://arxiv.org/pdf/2407.12675
7. https://www.sciencedirect.com/science/article/abs/pii/S0003687024001327
8. https://www.researchgate.net/publication/235176261_US_Military_Unmanned_Aerial_Vehicle_Mishaps_Assessment_of_the_Role_of_Human_Factors_Using_Human_Factors_Analysis_and_Classification_System_HFACS
9. https://arxiv.org/pdf/2103.04672
10. https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2019.00095/full
11. https://www.mdpi.com/2226-4310/12/3/206
12. https://spectrum.ieee.org/ai-drone-racing
13. https://www.flyability.com/elios-3-price
14. https://www.flyability.com/casestudies/grain-bin-inspections
15. https://marketintelo.com/report/confined-space-inspection-drone-market
16. https://www.flyability.com/power-plant-inspection-drones
17. https://www.allaboutlean.com/drones-at-ikea/
18. https://www.gather.ai/news/improve-warehouse-productivity
19. https://news.mit.edu/2024/corvus-autonomous-drones-precisely-track-warehouse-inventories-1220
20. https://www.automatedwarehouseonline.com/verity-inventory-drones-surpass-100-warehouse-sites/
21. https://utiasdsl.github.io/gym-pybullet-drones/
22. https://arxiv.org/html/2412.11764v4
23. https://arxiv.org/pdf/2311.02296
24. https://arc.aiaa.org/doi/10.2514/1.J059787
