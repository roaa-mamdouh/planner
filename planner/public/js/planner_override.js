// Copyright (c) 2024, ONFUSE AG and contributors
// For license information, please see license.txt

// Direct override for Planner task assignment functionality
frappe.provide("planner.override");

// Override onLoad to replace the problematic assignment function
$(document).ready(function() {
    console.log("Planner assignment override loaded");
    
    // Direct patch of frappe.call
    const originalFrappeCall = frappe.call;
    frappe.call = function(opts) {
        // Check if this is a call to assign a task
        if (opts && opts.method === "frappe.desk.form.assign_to.add" && 
            opts.args && opts.args.doctype === "Task") {
            
            console.log("INTERCEPTED TASK ASSIGNMENT:", opts.args);
            
            // Call our custom API method
            return $.ajax({
                url: "/api/method/planner.api.planner_assign_task",
                type: "POST",
                data: {
                    task: opts.args.name,
                    assign_to: Array.isArray(opts.args.assign_to) ? opts.args.assign_to[0] : opts.args.assign_to
                },
                success: function(data) {
                    console.log("Assignment successful", data);
                    if (opts.callback) opts.callback({message: {status: "ok"}});
                    if (opts.onSuccess) opts.onSuccess({message: {status: "ok"}});
                },
                error: function(xhr, status, error) {
                    console.error("Assignment failed", error);
                    if (opts.onError) opts.onError(error);
                }
            });
        }
        
        // Not an assignment call, proceed normally
        return originalFrappeCall(opts);
    };
}); 