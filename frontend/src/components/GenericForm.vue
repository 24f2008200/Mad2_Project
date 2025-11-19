<template>
    <div class="generic-form-card">
        <h5 class="form-title mb-3">{{ title }}</h5>

        <form @submit.prevent="onSave">
            <div class="row g-3">

                <template v-for="field in fields" :key="field.key">

                    <!-- 🔹 Read-only fields -->
                    <div v-if="field.type === 'noedit'" class="col-md-6">
                        <label class="form-label">{{ field.label }}</label>
                        <div class="form-control-plaintext">{{ localRow[field.key] }}</div>
                    </div>

                    <!-- 🔹 Password — auto creates confirm field -->
                    <!-- PASSWORD (two-column layout) -->
                    <div v-else-if="field.type === 'password'" class="col-12">
                        <div class="row g-3">

                            <!-- Password -->
                            <div class="col-md-6">
                                <label class="form-label">{{ field.label }}</label>
                                
                                <input type="password" class="form-control" v-model="localRow[field.key]"
                                    autocomplete="new-password" :required="field.required" />

                                <!-- Message under password (optional) -->
                                <div class="small mt-1" :class="passwordStatus(field.key)">
                                    {{ passwordMessage(field.key) }}
                                </div>
                            </div>
                            

                            <!-- Confirm Password -->
                            <div class="col-md-6">
                                <label class="form-label">Confirm {{ field.label }}</label>
                                <input type="password" class="form-control" v-model="passwordConfirm[field.key]"
                                    autocomplete="new-password" :required="field.required" />

                                <!-- Message under confirm -->
                                <div class="small mt-1" :class="passwordStatus(field.key)">
                                    {{ passwordMessage(field.key) }}
                                </div>
                            </div>

                        </div>
                        <div class="text-muted small">
                                Leave both fields empty to keep your current password unchanged.
                            </div>
                    </div>

                    <!-- 🔹 Text, Number, Email, Tel, Date, Textarea, Select -->
                    <div v-else class="col-md-6">
                        <label class="form-label">{{ field.label }}</label>

                        <!-- Text -->
                        <input v-if="field.type === 'text'" type="text" class="form-control"
                            v-model="localRow[field.key]" :required="field.required"/>

                        <!-- Number -->
                        <input v-else-if="field.type === 'number'" type="number" class="form-control"
                            v-model.number="localRow[field.key]" :required="field.required"/>

                        <!-- Email -->
                        <input v-else-if="field.type === 'email'" type="email" class="form-control"
                            v-model="localRow[field.key]" @blur="validateEmail(field.key)" />
                        <div v-if="emailErrors[field.key]" class="text-danger small">
                            {{ emailErrors[field.key] }}
                        </div>

                        <!-- Mobile -->
                        <input v-else-if="field.type === 'tel'" type="tel" maxlength="10" pattern="[0-9]{10}"
                            placeholder="10-digit mobile number" class="form-control" v-model="localRow[field.key]"
                            @input="validateMobile(field.key)" :required="field.required"/>
                        <div v-if="mobileErrors[field.key]" class="text-danger small">
                            {{ mobileErrors[field.key] }}
                        </div>

                        <!-- Date -->
                        <input v-else-if="field.type === 'date'" type="date" class="form-control"
                            v-model="localRow[field.key]" />

                        <!-- Select -->
                        <select v-else-if="field.type === 'select'" class="form-select" v-model="localRow[field.key]">
                            <option v-for="opt in field.options" :key="opt.value || opt" :value="opt.value || opt">
                                {{ opt.label || opt }}
                            </option>
                        </select>

                        <!-- Textarea -->
                        <textarea v-else-if="field.type === 'textarea'" class="form-control" rows="3"
                            v-model="localRow[field.key]"></textarea>

                        <!-- URL -->
                        <input v-else-if="field.type === 'url'" type="url" class="form-control"
                            placeholder="https://example.com" v-model="localRow[field.key]"
                            @blur="validateURL(field.key)" />

                        <div v-if="urlErrors[field.key]" class="text-danger small">
                            {{ urlErrors[field.key] }}
                        </div>


                        <!-- Fallback -->
                        <!-- <input v-else type="text" class="form-control"
              v-model="localRow[field.key]" /> -->
                    </div>

                </template>
            </div>

            <!-- ACTION BUTTONS -->
            <div class="mt-4">
                <button type="submit" class="btn btn-primary me-2">Save</button>
                <button type="button" class="btn btn-secondary" @click="emit('cancel')">
                    Cancel
                </button>
            </div>
        </form>
    </div>
</template>

<script setup>
import { reactive, watchEffect } from "vue";
import { cloneDeep } from "lodash-es";

const props = defineProps({
    row: { type: Object, required: true },
    fields: { type: Array, required: true },
    title: { type: String, default: "Edit Record" },
});

const emit = defineEmits(["save", "cancel"]);

const localRow = reactive({ ...props.row });

// ---------------------------
// PASSWORD CONFIRMATION LOGIC
// ---------------------------
const passwordConfirm = reactive({});
const passwordMessage = (key) => {
    const p = localRow[key];
    const c = passwordConfirm[key];
    if (!p && !c) return "";
    return p === c ? "Passwords match" : "Passwords do not match";
};
const passwordStatus = (key) => {
    const p = localRow[key];
    const c = passwordConfirm[key];
    if (!p && !c) return "";
    return p === c ? "text-success" : "text-danger";
};

// ---------------------------
// EMAIL VALIDATION
// ---------------------------
const emailErrors = reactive({});
function validateEmail(key) {
    const val = localRow[key];
    if (!val) {
        emailErrors[key] = "";
        return;
    }
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    emailErrors[key] = pattern.test(val) ? "" : "Invalid email format";
}

// ---------------------------
// MOBILE VALIDATION
// ---------------------------
const mobileErrors = reactive({});
function validateMobile(key) {
    const val = localRow[key];
    mobileErrors[key] =
        /^\d{10}$/.test(val) ? "" : "Mobile number must be 10 digits";
}

// ---------------------------
// SYNC PROPS
// ---------------------------
watchEffect(() => {
    Object.assign(localRow, props.row);
});

// ---------------------------
// URL VALIDATION
// ---------------------------
const urlErrors = reactive({});

function validateURL(key) {
    const val = localRow[key];
    if (!val) {
        urlErrors[key] = "";
        return;
    }

    const pattern = /^(https?:\/\/)[^\s$.?#].[^\s]*$/i;

    urlErrors[key] = pattern.test(val)
        ? ""
        : "Invalid URL format. Must start with http:// or https://";
}

// ---------------------------
// SUBMIT HANDLER
// ---------------------------
function onSave() {
  for (const field of props.fields) {
    if (field.type === "password") {
      const key = field.key;
      const newPassword = localRow[key]?.trim();
      const confirmPassword = passwordConfirm[key]?.trim();

      // CASE 1: Both empty → user is NOT changing password
      if (!newPassword && !confirmPassword) {
        delete localRow[key];            // do not send empty password
        continue;                        // skip validation
      }

      // CASE 2: Only one field has data → invalid
      if ((newPassword && !confirmPassword) || (!newPassword && confirmPassword)) {
        alert("Please fill both password fields.");
        return;
      }

      // CASE 3: Both filled but do NOT match
      if (newPassword !== confirmPassword) {
        alert("Passwords do not match.");
        return;
      }

      // CASE 4: Valid → save normally
    }
  }

//   emit("save", { ...localRow });
emit("save", cloneDeep(localRow));

}

</script>
<style scoped>
.generic-form-card {
    max-width: 650px;
    /* avoids full-width stretch */
    margin: 0 auto;
    /* center horizontally */
    background: #fff;
    padding: 25px 35px;
    border-radius: 12px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
}

.form-title {
    text-align: center;
    font-weight: 600;
    font-size: 1.25rem;
    color: #222;
    margin-bottom: 20px;
}

@media (max-width: 576px) {
    .generic-form-card {
        padding: 20px 16px;
        max-width: 100%;
    }
}
</style>