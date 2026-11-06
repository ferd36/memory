const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('api', {
  getProblemTypes: () => ipcRenderer.invoke('get-problem-types'),
  createProblem: (type, round) => ipcRenderer.invoke('create-problem', type, round),
  evaluateProblem: (type, solution, userInput, state) =>
    ipcRenderer.invoke('evaluate-problem', type, solution, userInput, state)
})
