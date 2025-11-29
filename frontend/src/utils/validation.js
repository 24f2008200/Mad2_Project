export function validateField(value, rules = []) {
  const errors = [];

  for (const rule of rules) {
    // String rules
    if (rule === "required") {
      if (!value && value !== 0) errors.push("This field is required.");
    }
    if (rule === "passwordMatch") {
      const p = value?.password || "";
      const c = value?.confirm || "";

      // user did NOT attempt to change password → accept empty
      if (p === "" && c === "") continue;

      if (p.length < 3)
        errors.push("Password must be at least 3 characters.");

      if (p !== c)
        errors.push("Passwords do not match.");
    }


    if (rule === "email") {
      if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))
        errors.push("Invalid email format.");
    }

    // Object rules: { min: 3 } , { max: 10 }
    if (typeof rule === "object") {
      if (rule.min !== undefined) {
        if (String(value).length < rule.min) {
          errors.push(`Minimum length is ${rule.min}.`);
        }
      }

      if (rule.max !== undefined) {
        if (String(value).length > rule.max) {
          errors.push(`Maximum length is ${rule.max}.`);
        }
      }

      if (rule.custom) {
        const result = rule.custom(value);
        if (result !== true) {
          errors.push(result); // custom error message
        }
      }
    }
  }

  return errors;
}

export function validateForm(form, schema) {
  const allErrors = {};

  schema.sections.forEach(section => {
    section.fields.forEach(field => {
      if (field.rules) {
        const value = form[field.model];
        const fieldErrors = validateField(value, field.rules);
        if (fieldErrors.length) {
          allErrors[field.model] = fieldErrors;
        }
      }
    });
  });

  return allErrors;
}
