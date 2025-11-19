export const userCols = [
  { key: "id", label: "ID", type: "noedit" },
  { key: "name", label: "Name", type: "text" },
  { key: "mobile", label: "Mobile", type: "number" },
  { key: "address", label: "Address", type: "text" },
  { key: "email", label: "E-Mail", type: "text" },
  { key: "rev", label: "Revenue" },
  { key: "last_login", label: "Last Seen" },
  { key: "edit", label: "Edit", type: "action" },
];

export const reservationCols = [
  { key: "id", label: "ID", type: "noedit" },
  { key: "label", label: "Spot", type: "text" },
  { key: "user_name", label: "User", type: "text" },
  { key: "vehicle_number", label: "Vehicle", type: "text" },
  { key: "start_time", label: "From", type: "text" },
  { key: "end_time", label: "To", type: "text" },
  { key: "driver_name", label: "Driver", type: "text" },
  { key: "driver_contact", label: "Contact", type: "number" },
  { key: "total_earnings", label: "Revenue", type: "number" },
  { key: "edit", label: "Edit", type: "action" },
];

export const lotCols = [
  { key: "id", label: "ID", type: "noedit" },
  { key: "name", label: "Name", type: "text" },
  { key: "address", label: "Address", type: "text" },
  { key: "available_spots", label: "Available", type: "number" },
  { key: "occupied_spots", label: "Occupied", type: "number" },
  { key: "price", label: "Price", type: "number" },
  { key: "edit", label: "Edit", type: "action" },
];

export const reminderCols = [
  { key: "id", label: "ID", type: "noedit" },
  { key: "user_id", label: "User ID", type: "number" },
  { key: "user_name", label: "User", type: "text" },
  { key: "scheduled_at", label: "Scheduled", type: "text" },
  { key: "status", label: "Status", type: "text" },
  { key: "sent_at", label: "Sent At", type: "text" },
  { key: "error_message", label: "Error", type: "text" },
];

export const columnsMap = {
  user: userCols,
  reservation: reservationCols,
  lot: lotCols,
  reminder: reminderCols,
};
