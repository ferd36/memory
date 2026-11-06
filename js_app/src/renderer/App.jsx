import React, { useState, useEffect, useRef } from 'react'

export default function App() {
  const [phase, setPhase] = useState('selection') // selection, memorize, recall, feedback
  const [types, setTypes] = useState([])
  const [problem, setProblem] = useState(null)
  const [answer, setAnswer] = useState('')
  const [evaluation, setEvaluation] = useState(null)
  const [currentType, setCurrentType] = useState(null)
  const [round, setRound] = useState(1)
  // Bumped when a game starts or ends. A bridge call that resolves after the
  // player quit belongs to an old game and must not change state.
  const gameRef = useRef(0)
  // True while Next is loading a round. The button stays on screen during the
  // bridge call, and a second press must not start another round.
  const advancingRef = useRef(false)
  const MAX_ROUNDS = 10

  useEffect(() => {
    window.api.getProblemTypes().then(setTypes).catch(console.error)
  }, [])

  const startProblemType = async (type) => {
    const game = ++gameRef.current
    setCurrentType(type)
    await loadRound(type, 1, game)
  }

  const loadRound = async (type, r, game = gameRef.current) => {
    const p = await window.api.createProblem(type, r)
    if (game !== gameRef.current) return
    setRound(r)
    setProblem(p)
    setAnswer('')
    setPhase('memorize')
  }

  const handleNext = async () => {
    if (advancingRef.current) return
    advancingRef.current = true
    try {
      if (round < MAX_ROUNDS) {
        await loadRound(currentType, round + 1)
      } else {
        handleQuit()
      }
    } finally {
      advancingRef.current = false
    }
  }

  const handleQuit = () => {
    gameRef.current += 1
    setPhase('selection')
    setProblem(null)
    setCurrentType(null)
    setRound(1)
  }

  return (
    <div className="card">
      {phase === 'selection' && <SelectionScreen types={types} onSelect={startProblemType} />}
      {phase === 'memorize' && <MemorizeScreen problem={problem} round={round} totalRounds={MAX_ROUNDS} onComplete={() => setPhase('recall')} onQuit={handleQuit} />}
      {phase === 'recall' && <RecallScreen problem={problem} round={round} totalRounds={MAX_ROUNDS} onSubmit={async (ans) => {
        const game = gameRef.current
        let evalResult
        try {
          evalResult = await window.api.evaluateProblem(
            problem.type_id, problem.solution, ans, problem.state)
        } catch (e) {
          // Fallback if evaluation fails
          const isCorrect = ans.trim().toLowerCase() === problem.solution.trim().toLowerCase()
          evalResult = { score: isCorrect ? 1 : 0, correct: isCorrect, fallback: true }
        }
        if (game !== gameRef.current) return
        setAnswer(ans)
        setEvaluation(evalResult)
        setPhase('feedback')
      }} onQuit={handleQuit} />}
      {phase === 'feedback' && <FeedbackScreen problem={problem} answer={answer} evaluation={evaluation} round={round} totalRounds={MAX_ROUNDS} onNext={handleNext} onQuit={handleQuit} />}
    </div>
  )
}

function SelectionScreen({ types, onSelect }) {
  return (
    <div>
      <h1>Memory Trainer</h1>
      <h2>Select a Game</h2>
      <div className="grid">
        {types.map(t => (
          <button key={t.id} className="btn" onClick={() => onSelect(t.id)}>
            {t.name}
          </button>
        ))}
      </div>
    </div>
  )
}

function MemorizeScreen({ problem, round, totalRounds, onComplete, onQuit }) {
  const [scale, setScale] = useState(1)
  const [timeLeft, setTimeLeft] = useState((problem.exposure_ms / 1000).toFixed(2))

  useEffect(() => {
    const startTime = Date.now()
    
    // Smooth progress bar animation
    const frame = requestAnimationFrame(() => {
      requestAnimationFrame(() => setScale(0))
    })
    
    // Countdown text update
    let timerFrame;
    const updateTimer = () => {
      const elapsed = Date.now() - startTime
      const remaining = Math.max(0, problem.exposure_ms - elapsed)
      setTimeLeft((remaining / 1000).toFixed(2))
      if (remaining > 0) {
        timerFrame = requestAnimationFrame(updateTimer)
      }
    }
    timerFrame = requestAnimationFrame(updateTimer)
    
    // End of phase
    const timer = setTimeout(onComplete, problem.exposure_ms)
    
    return () => {
      cancelAnimationFrame(frame)
      cancelAnimationFrame(timerFrame)
      clearTimeout(timer)
    }
  }, [problem, onComplete])

  const renderMemorizeText = () => {
    if (problem.type_id === 'ColorSequence') {
      return problem.memorize.split('').map((char, i) => {
        let color = 'inherit'
        if (char === 'R') color = '#ff4444' // bright red
        if (char === 'G') color = '#44ff44' // bright green
        if (char === 'B') color = '#4488ff' // bright blue
        if (char === 'Y') color = '#ffff44' // bright yellow
        return <span key={i} style={{ color, textShadow: '0 2px 4px rgba(0,0,0,0.5)' }}>{char}</span>
      })
    }
    if (problem.type_id === 'PlayingCardSequence') {
      return problem.memorize.split('').map((char, i) => {
        if (char === '♥' || char === '♦') {
          return <span key={i} style={{ color: '#ff4444' }}>{char}</span>
        }
        return <span key={i}>{char}</span>
      })
    }
    if (problem.type_id === 'MatrixMemory') {
      const rows = problem.memorize.split('\n').map(row => row.split(' '))
      const cols = rows[0].length
      
      return (
        <table className="matrix-grid">
          <thead>
            <tr>
              <th></th>
              {Array.from({length: cols}).map((_, i) => (
                <th key={i}>{String.fromCharCode(65 + i)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, r) => (
              <tr key={r}>
                <th>{r + 1}</th>
                {row.map((cell, c) => (
                  <td key={c} className={cell !== '.' ? 'marked' : ''}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )
    }
    return problem.memorize
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', opacity: 0.7, marginBottom: '1rem' }}>
        <div>Round {round} / {totalRounds}</div>
        <div style={{ cursor: 'pointer', textDecoration: 'underline' }} onClick={onQuit}>Quit Game</div>
      </div>
      <h2>Memorize</h2>
      <div className={`memorize-text ${problem.memorize.includes('\n') ? 'multiline' : ''}`} style={{whiteSpace: 'pre-wrap'}}>
        {renderMemorizeText()}
      </div>
      <div className="progress-bar-container">
        <div 
          className="progress-bar" 
          style={{ transition: `transform ${problem.exposure_ms}ms linear`, transform: `scaleX(${scale})` }} 
        />
      </div>
      <div style={{marginTop: '0.5rem', opacity: 0.8, fontSize: '0.9rem', textAlign: 'right'}}>
        {timeLeft}s remaining
      </div>
    </div>
  )
}

function RecallScreen({ problem, round, totalRounds, onSubmit, onQuit }) {
  const [input, setInput] = useState('')
  const [timeSpent, setTimeSpent] = useState("0.00")
  const isMultiline = problem.input_type === 'multiline'

  useEffect(() => {
    const startTime = Date.now()
    let frameId;
    const updateTimer = () => {
      setTimeSpent(((Date.now() - startTime) / 1000).toFixed(2))
      frameId = requestAnimationFrame(updateTimer)
    }
    frameId = requestAnimationFrame(updateTimer)
    return () => cancelAnimationFrame(frameId)
  }, [])
  
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', opacity: 0.7, marginBottom: '1rem' }}>
        <div>Round {round} / {totalRounds}</div>
        <div style={{ cursor: 'pointer', textDecoration: 'underline' }} onClick={onQuit}>Quit Game</div>
      </div>
      <h2 style={{whiteSpace: 'pre-wrap'}}>{problem.prompt}</h2>
      <form onSubmit={(e) => { e.preventDefault(); onSubmit(input); }}>
        {isMultiline ? (
          // NameList has a newline-joined solution, and the player can enter it
          // one name per line.
          <textarea
            autoFocus
            rows={Math.max(3, problem.solution.split('\n').length)}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              // Enter inserts a newline; Cmd/Ctrl+Enter submits.
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault()
                onSubmit(input)
              }
            }}
            placeholder="One per line — ⌘/Ctrl+Enter to submit"
          />
        ) : (
          <input
            type="text"
            autoFocus
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Type your answer here..."
          />
        )}
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div style={{opacity: 0.8, fontSize: '0.9rem'}}>Time: {timeSpent}s</div>
          <button type="submit" className="btn">Submit</button>
        </div>
      </form>
    </div>
  )
}

function FeedbackScreen({ problem, answer, evaluation, round, totalRounds, onNext, onQuit }) {
  const isCorrect = evaluation ? evaluation.correct : false
  const isScored = problem.is_scored !== false
  
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', opacity: 0.7, marginBottom: '1rem' }}>
        <div>Round {round} / {totalRounds}</div>
        <div style={{ cursor: 'pointer', textDecoration: 'underline' }} onClick={onQuit}>Quit Game</div>
      </div>
      {!isScored ? (
        <div className="feedback correct">
          Warmup round complete!
        </div>
      ) : (
        <div className={`feedback ${isCorrect ? 'correct' : 'incorrect'}`}>
          {isCorrect ? '✓ Correct!' : '✗ Incorrect'}
        </div>
      )}
      {isScored && evaluation && evaluation.fallback && (
        <p className="warning">The scorer did not respond, so this answer was checked for an exact match only.</p>
      )}
      {isScored && <p>Expected: <strong style={{ whiteSpace: 'pre-wrap' }}>{problem.solution}</strong></p>}
      {answer && isScored && <p>You typed: <strong style={{ whiteSpace: 'pre-wrap' }}>{answer}</strong></p>}
      
      <button className="btn" onClick={onNext} style={{ marginTop: '2rem' }} autoFocus>
        {round < totalRounds ? 'Next Round' : 'Finish Game'}
      </button>
    </div>
  )
}
