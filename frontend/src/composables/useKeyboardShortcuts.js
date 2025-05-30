import { onMounted, onUnmounted } from 'vue'

export function useKeyboardShortcuts() {
  let shortcuts = {}
  
  const setupKeyboardShortcuts = (shortcutConfig) => {
    shortcuts = { ...shortcutConfig }
    
    // Add event listener
    document.addEventListener('keydown', handleKeyDown)
  }
  
  const handleKeyDown = (event) => {
    // Don't trigger shortcuts when typing in inputs
    if (event.target.tagName === 'INPUT' || 
        event.target.tagName === 'TEXTAREA' || 
        event.target.contentEditable === 'true') {
      return
    }
    
    const key = event.key.toLowerCase()
    const ctrl = event.ctrlKey || event.metaKey
    const shift = event.shiftKey
    const alt = event.altKey
    
    // Build shortcut key
    let shortcutKey = ''
    if (ctrl) shortcutKey += 'ctrl+'
    if (shift) shortcutKey += 'shift+'
    if (alt) shortcutKey += 'alt+'
    shortcutKey += key
    
    // Handle common shortcuts
    if (ctrl && key === 'a' && shortcuts.onSelectAll) {
      event.preventDefault()
      shortcuts.onSelectAll()
      return
    }
    
    if (key === 'delete' && shortcuts.onDelete) {
      event.preventDefault()
      shortcuts.onDelete()
      return
    }
    
    if (key === 'escape' && shortcuts.onEscape) {
      event.preventDefault()
      shortcuts.onEscape()
      return
    }
    
    if (ctrl && key === 'z' && shortcuts.onUndo) {
      event.preventDefault()
      shortcuts.onUndo()
      return
    }
    
    if (ctrl && key === 'y' && shortcuts.onRedo) {
      event.preventDefault()
      shortcuts.onRedo()
      return
    }
    
    if (ctrl && key === 'c' && shortcuts.onCopy) {
      event.preventDefault()
      shortcuts.onCopy()
      return
    }
    
    if (ctrl && key === 'v' && shortcuts.onPaste) {
      event.preventDefault()
      shortcuts.onPaste()
      return
    }
    
    if (ctrl && key === 'f' && shortcuts.onFind) {
      event.preventDefault()
      shortcuts.onFind()
      return
    }
    
    // Arrow key navigation
    if (key === 'arrowup' && shortcuts.onArrowUp) {
      event.preventDefault()
      shortcuts.onArrowUp()
      return
    }
    
    if (key === 'arrowdown' && shortcuts.onArrowDown) {
      event.preventDefault()
      shortcuts.onArrowDown()
      return
    }
    
    if (key === 'arrowleft' && shortcuts.onArrowLeft) {
      event.preventDefault()
      shortcuts.onArrowLeft()
      return
    }
    
    if (key === 'arrowright' && shortcuts.onArrowRight) {
      event.preventDefault()
      shortcuts.onArrowRight()
      return
    }
    
    // Space for play/pause or selection
    if (key === ' ' && shortcuts.onSpace) {
      event.preventDefault()
      shortcuts.onSpace()
      return
    }
    
    // Enter for confirm/edit
    if (key === 'enter' && shortcuts.onEnter) {
      event.preventDefault()
      shortcuts.onEnter()
      return
    }
    
    // Tab for navigation
    if (key === 'tab' && shortcuts.onTab) {
      event.preventDefault()
      shortcuts.onTab(shift)
      return
    }
    
    // Number keys for quick actions
    if (/^[0-9]$/.test(key) && shortcuts.onNumber) {
      event.preventDefault()
      shortcuts.onNumber(parseInt(key))
      return
    }
    
    // Custom shortcuts
    if (shortcuts[shortcutKey]) {
      event.preventDefault()
      shortcuts[shortcutKey]()
    }
  }
  
  const cleanup = () => {
    document.removeEventListener('keydown', handleKeyDown)
  }
  
  // Auto cleanup on unmount
  onUnmounted(() => {
    cleanup()
  })
  
  return {
    setupKeyboardShortcuts,
    cleanup
  }
}
