# RogueSignalProtocol - Key Assumptions

## Enemy Movement System
- **ALL enemy movement MUST use the movement queue system**
- Enemies calculate their intended path/moves and store them in a queue
- Movement prediction shows the contents of this queue to the player
- On each turn, enemies execute the first item from their queue
- Queues are updated when targets change or paths become invalid
- This applies to ALL movement types: RANDOM, SEEK, TRACK, LINEAR

## Enemy Vision and Targeting
- If an enemy can see the player directly, that becomes their "last known location"
- Enemy alerts from other enemies are only useful if the enemy cannot currently see the player
- When an enemy becomes hostile, they should immediately pathfind to their target and populate their movement queue

## Code Clarity
- Use clear, descriptive variable names
- Add useful comments explaining the purpose of each system
- Keep systems simple and maintainable
- Avoid complex nested logic where possible

## Library Dependencies
- **ALWAYS use the latest version of python-tcod library**
- When encountering API errors, check documentation first before attempting complex fixes
- Modern TCOD uses SimpleGraph and boolean cost arrays, not numpy_array functions