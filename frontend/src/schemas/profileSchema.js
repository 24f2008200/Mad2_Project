export const profileSchema = {
  tabs: [
    { id: "profile", title: "Profile Info" },
    { id: "ops", title: "Operational Data" }
  ],
 
  sections: [
    {
      id: "profile",
      tab: "profile",
      label: "User Info",
      fields: [
        { model: "name", label: "Name", type: "text", rules: ["required"] },
        { model: "email", label: "Email", type: "email", rules: ["required", "email"] },
        { model: "mobile", label: "Phone", type: "text", rules: [{ min: 10 }, { max: 10 }] },
        { model: "address", label: "Address", type: "textarea" },
        { model: "receive_reminders", label: "Receive Reminders", type: "checkbox" },
        { model: "reminder_time", label: "Reminder Time", type: "time", dependsOn: { model: "receive_reminders", value: true } },
        { model: "google_chat_webhook", label: "Google Chat Webhook URL", type: "text" },
        { model: "password_group",label: "Password",type: "password-group",rules: ["passwordMatch"]},

        { model: "is_admin", type: "checkbox", label: "Admin User", adminOnly: true },
        { model: "is_blocked", type: "checkbox", label: "Blocked", adminOnly: true }
      ]
    },

    {
      id: "ops",
      tab: "ops",
      label: "User Activity",
      fields: [
        { model: "total_reservations", label: "Reservations", type: "number" },
        { model: "active_reservations", label: "Active", type: "text" },
        { model: "billing", label: "Billing", type: "text" },
        { model: "last_active", label: "Last Active", type: "text" }
      ]
    }
  ]
};
