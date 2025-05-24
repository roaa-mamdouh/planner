// Copyright (c) 2024, ONFUSE AG and contributors
// For license information, please see license.txt

// Patch for Planner frontend to use our custom API for assignment
(function() {
    console.log("Initializing Planner fixes...");
    
    // Monkeypatch frappe.call to intercept assign_to.add calls
    const originalFrappeCall = frappe.call;
    frappe.call = function(opts) {
        // Check if this is a call to assign a task
        if (opts && opts.method === "frappe.desk.form.assign_to.add" && 
            opts.args && opts.args.doctype === "Task") {
            
            console.log("Intercepting task assignment call", opts.args);
            
            // Replace with our custom API call
            return originalFrappeCall({
                method: "planner.api.planner_assign_task",
                args: {
                    task: opts.args.name,
                    assign_to: opts.args.assign_to[0]
                },
                callback: function(response) {
                    if (response.message && response.message.success) {
                        console.log("Task assigned successfully to", response.message.user);
                        
                        // Create a compatible response to what the original call would have expected
                        const modifiedResponse = {
                            message: {
                                status: "ok"
                            }
                        };
                        
                        // Call the original success callback with a compatible response
                        if (opts.callback) opts.callback(modifiedResponse);
                        if (opts.onSuccess) opts.onSuccess(modifiedResponse);
                    } else {
                        console.error("Task assignment failed:", response);
                        // Call the original error callback
                        if (opts.onError) opts.onError(response);
                    }
                },
                error: function(response) {
                    console.error("Task assignment error:", response);
                    if (opts.onError) opts.onError(response);
                }
            });
        }
        
        // Not an assignment call, proceed normally
        return originalFrappeCall(opts);
    };
    
    // Add event listener to detect when the timeline is rendered
    document.addEventListener('DOMContentLoaded', function() {
        // Check periodically if the timeline is ready
        const checkInterval = setInterval(function() {
            if (window.vis && document.querySelector('.vis-timeline')) {
                clearInterval(checkInterval);
                console.log("Timeline detected, fixing timeline drag behavior");
                
                // Add custom styling to make sure drag and drop works properly
                const style = document.createElement('style');
                style.textContent = `
                    .vis-item.vis-selected {
                        z-index: 999 !important;
                    }
                `;
                document.head.appendChild(style);
            }
        }, 1000);
    });
    
    console.log("✅ Planner fixes applied successfully");
})(); 