import { ref, computed, nextTick } from 'vue'

export function useVirtualization() {
  // State
  const containerRef = ref(null)
  const scrollTop = ref(0)
  const scrollLeft = ref(0)
  const containerHeight = ref(0)
  const containerWidth = ref(0)
  const itemHeight = ref(60) // Default row height
  const itemWidth = ref(200) // Default item width
  const items = ref([])
  
  // Buffer for smooth scrolling
  const bufferSize = 5
  
  // Computed properties
  const visibleStartIndex = computed(() => {
    return Math.max(0, Math.floor(scrollTop.value / itemHeight.value) - bufferSize)
  })
  
  const visibleEndIndex = computed(() => {
    const visibleCount = Math.ceil(containerHeight.value / itemHeight.value)
    return Math.min(items.value.length - 1, visibleStartIndex.value + visibleCount + bufferSize * 2)
  })
  
  const visibleItems = computed(() => {
    return items.value.slice(visibleStartIndex.value, visibleEndIndex.value + 1).map((item, index) => ({
      ...item,
      virtualIndex: visibleStartIndex.value + index,
      top: (visibleStartIndex.value + index) * itemHeight.value
    }))
  })
  
  const totalHeight = computed(() => {
    return items.value.length * itemHeight.value
  })
  
  const visibleHorizontalStartIndex = computed(() => {
    return Math.max(0, Math.floor(scrollLeft.value / itemWidth.value) - bufferSize)
  })
  
  const visibleHorizontalEndIndex = computed(() => {
    const visibleCount = Math.ceil(containerWidth.value / itemWidth.value)
    return Math.min(items.value.length - 1, visibleHorizontalStartIndex.value + visibleCount + bufferSize * 2)
  })
  
  // Setup virtualization
  const setupVirtualization = (container, itemList, options = {}) => {
    if (!container) return
    
    containerRef.value = container
    items.value = itemList || []
    
    // Update options
    if (options.itemHeight) itemHeight.value = options.itemHeight
    if (options.itemWidth) itemWidth.value = options.itemWidth
    
    // Get container dimensions
    updateContainerDimensions()
    
    // Setup scroll listener
    container.addEventListener('scroll', handleScroll, { passive: true })
    
    // Setup resize observer
    const resizeObserver = new ResizeObserver(updateContainerDimensions)
    resizeObserver.observe(container)
    
    // Store cleanup function
    container._virtualizationCleanup = () => {
      container.removeEventListener('scroll', handleScroll)
      resizeObserver.disconnect()
    }
  }
  
  const handleScroll = (event) => {
    const container = event.target
    scrollTop.value = container.scrollTop
    scrollLeft.value = container.scrollLeft
  }
  
  const updateContainerDimensions = () => {
    if (!containerRef.value) return
    
    const rect = containerRef.value.getBoundingClientRect()
    containerHeight.value = rect.height
    containerWidth.value = rect.width
  }
  
  // Scroll to specific item
  const scrollToItem = (index, behavior = 'smooth') => {
    if (!containerRef.value || index < 0 || index >= items.value.length) return
    
    const targetScrollTop = index * itemHeight.value
    
    containerRef.value.scrollTo({
      top: targetScrollTop,
      behavior
    })
  }
  
  // Scroll to specific position
  const scrollToPosition = (top, left = null, behavior = 'smooth') => {
    if (!containerRef.value) return
    
    const scrollOptions = { top, behavior }
    if (left !== null) scrollOptions.left = left
    
    containerRef.value.scrollTo(scrollOptions)
  }
  
  // Get item position
  const getItemPosition = (index) => {
    return {
      top: index * itemHeight.value,
      height: itemHeight.value
    }
  }
  
  // Check if item is visible
  const isItemVisible = (index) => {
    return index >= visibleStartIndex.value && index <= visibleEndIndex.value
  }
  
  // Update items
  const updateItems = (newItems) => {
    items.value = newItems || []
  }
  
  // Get visible range
  const getVisibleRange = () => {
    return {
      start: visibleStartIndex.value,
      end: visibleEndIndex.value,
      items: visibleItems.value
    }
  }
  
  // Estimate scroll position for item
  const estimateScrollPosition = (itemId) => {
    const index = items.value.findIndex(item => item.id === itemId)
    if (index === -1) return null
    
    return getItemPosition(index)
  }
  
  // Smooth scroll to item by ID
  const scrollToItemById = (itemId, behavior = 'smooth') => {
    const index = items.value.findIndex(item => item.id === itemId)
    if (index !== -1) {
      scrollToItem(index, behavior)
    }
  }
  
  // Get container scroll info
  const getScrollInfo = () => {
    return {
      scrollTop: scrollTop.value,
      scrollLeft: scrollLeft.value,
      containerHeight: containerHeight.value,
      containerWidth: containerWidth.value,
      totalHeight: totalHeight.value,
      maxScrollTop: Math.max(0, totalHeight.value - containerHeight.value)
    }
  }
  
  // Handle dynamic item heights (for complex layouts)
  const itemHeights = ref(new Map())
  
  const setItemHeight = (index, height) => {
    itemHeights.value.set(index, height)
  }
  
  const getItemHeight = (index) => {
    return itemHeights.value.get(index) || itemHeight.value
  }
  
  const calculateDynamicPositions = () => {
    const positions = []
    let currentTop = 0
    
    for (let i = 0; i < items.value.length; i++) {
      positions[i] = {
        top: currentTop,
        height: getItemHeight(i)
      }
      currentTop += getItemHeight(i)
    }
    
    return positions
  }
  
  // Performance optimization: throttle scroll updates
  let scrollUpdateTimeout = null
  
  const throttledScrollUpdate = (callback, delay = 16) => {
    if (scrollUpdateTimeout) {
      clearTimeout(scrollUpdateTimeout)
    }
    
    scrollUpdateTimeout = setTimeout(callback, delay)
  }
  
  // Cleanup function
  const cleanup = () => {
    if (containerRef.value && containerRef.value._virtualizationCleanup) {
      containerRef.value._virtualizationCleanup()
    }
    
    if (scrollUpdateTimeout) {
      clearTimeout(scrollUpdateTimeout)
    }
  }
  
  // Auto-cleanup when container changes
  const previousContainer = ref(null)
  
  const watchContainer = () => {
    if (previousContainer.value && previousContainer.value._virtualizationCleanup) {
      previousContainer.value._virtualizationCleanup()
    }
    previousContainer.value = containerRef.value
  }
  
  return {
    // State
    containerRef,
    scrollTop,
    scrollLeft,
    containerHeight,
    containerWidth,
    itemHeight,
    itemWidth,
    items,
    
    // Computed
    visibleItems,
    visibleStartIndex,
    visibleEndIndex,
    totalHeight,
    
    // Methods
    setupVirtualization,
    updateItems,
    scrollToItem,
    scrollToItemById,
    scrollToPosition,
    getItemPosition,
    isItemVisible,
    getVisibleRange,
    estimateScrollPosition,
    getScrollInfo,
    
    // Dynamic heights
    setItemHeight,
    getItemHeight,
    calculateDynamicPositions,
    
    // Utilities
    cleanup,
    throttledScrollUpdate
  }
}
