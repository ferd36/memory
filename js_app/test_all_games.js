import { get_problem_types, create_problem } from './src/main/problems.js'

async function runTests() {
  console.log("Starting exhaustive game generation tests...")
  let types = []
  try {
    types = get_problem_types()
    console.log(`Successfully fetched ${types.length} problem types.`)
  } catch (e) {
    console.error("FAILED to fetch problem types", e)
    process.exit(1)
  }

  let successCount = 0
  let failureCount = 0
  const failures = []

  for (const t of types) {
    try {
      const p = create_problem(t.id)
      if (!p.display_name || !p.memorize || !p.prompt || p.solution === undefined || !p.exposure_ms || !p.input_type) {
        throw new Error(`Missing fields in response: ${JSON.stringify(p)}`)
      }
      successCount++
    } catch (e) {
      console.error(`FAILED to create problem for ${t.id}:`, e.message)
      failureCount++
      failures.push(t.id)
    }
  }

  console.log(`\nTest Results: ${successCount} succeeded, ${failureCount} failed.`)
  if (failures.length > 0) {
    console.log("Failed games:", failures.join(", "))
    process.exit(1)
  } else {
    console.log("ALL GAMES TESTED SUCCESSFULLY!")
  }
}

runTests()
