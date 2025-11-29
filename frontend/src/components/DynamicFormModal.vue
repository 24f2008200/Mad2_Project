<template>
    <div class="modal fade" tabindex="-1" ref="modalEl">
        <div class="modal-dialog" :class="modalSize">
            <div class="modal-content">
                <!-- Header -->
                <div class="modal-header">
                    <h5 class="modal-title">{{ title }}</h5>
                    <button type="button" class="btn-close" @click="close"></button>
                </div>

                <!-- Body -->

                <div class="modal-body">

                    <div v-if="loading">Loading...</div>

                    <div v-else>
                        <!-- Tabs -->
                        <ul v-if="schema.tabs" class="nav nav-tabs mb-3">
                            <li v-for="tab in schema.tabs" :key="tab.id" class="nav-item">
                                <button class="nav-link" :class="{ active: activeTab === tab.id }"
                                    @click="activeTab = tab.id">
                                    {{ tab.title }}
                                </button>
                            </li>
                        </ul>

                        <div v-for="section in activeSections" :key="section.id" class="mb-3">
                            <h6 v-if="section.label" class="border-bottom pb-1">{{ section.label }}</h6>


                            <div class="row g-3">
                                <div v-for="field in visibleFields(section)" :key="field.model">
                                    <FieldRenderer :field="field" :errors="validationErrors[field.model] || []"
                                        v-model="form[field.model]" />
                                </div>
                            </div>

                        </div>

                        <!-- Messages -->
                        <div v-if="error" class="alert alert-danger mt-2">{{ error }}</div>
                        <div v-if="success" class="alert alert-success mt-2">{{ success }}</div>
                    </div>
                </div>

                <!-- Footer -->
                <div class="modal-footer">
                    <button class="btn btn-secondary" @click="close">Cancel</button>
                    <button class="btn btn-primary" :disabled="saving" @click="submit">Save</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { reactive, ref, watch, computed } from "vue";
import FieldRenderer from "./FieldRenderer.vue";
import { apiFetch } from "@/api";

const props = defineProps({
    show: Boolean,
    title: String,
    schema: Object,          // field + tab + section structure
    fetchUrl: String,        // GET endpoint
    submitUrl: String,       // POST/PUT endpoint
    method: { type: String, default: "POST" },
    modalSize: { type: String, default: "modal-lg" },
    context: Object,         // role checks, user info etc.
});

const emit = defineEmits(["closed", "saved"]);

// ---- STATE ----
const modalEl = ref(null);
let bsModal = null;

const loading = ref(false);
const saving = ref(false);
const error = ref("");
const success = ref("");

const form = reactive({});
const activeTab = ref(null);
const validationErrors = ref({});

console.log("DynamicFormModal props:", props);
// Filter sections based on active tab
const activeSections = computed(() => {
    if (!props.schema.tabs) return props.schema.sections;
    return props.schema.sections.filter(s => s.tab === activeTab.value);
});

// ---- Modal open/close ----
watch(() => props.show, async (val) => {
    if (!bsModal) {
        bsModal = new bootstrap.Modal(modalEl.value);
    }
    if (val) {
        await loadData();
        bsModal.show();
    } else {
        bsModal.hide();
    }
});

function close() {
    emit("closed");
}

// ---- Helpers ----
function shouldRender(field) {
    // console.log("Checking field:", field);
    // console.log("Logic:", !field);
    if (!field) return false;

    const isAdminUser = props.context?.isAdmin === true;

    if (field.adminOnly === true && !isAdminUser) {
        return false;
    }

    return true;
}

function visibleFields(section) {
    if (!section || !Array.isArray(section.fields)) return [];
    return section.fields.filter(f => shouldRender(f));
}



// ---- Data load ----
async function loadData() {
    loading.value = true;
    error.value = "";
    success.value = "";

    // initializeForm(props.schema);

    // assign initial active tab
    if (props.schema.tabs) activeTab.value = props.schema.tabs[0].id;

    // initialize form defaults
    props.schema.sections.forEach(section =>
        section.fields.forEach(field => {
            form[field.model] = field.default ?? "";
            // if (field.type === "password-group") {
            //     form[field.model] = { password: "", confirm: "" };
            // } else {
            //     form[field.model] = field.default ?? "";
            // }

        })
    );

    try {
        if (props.fetchUrl) {
            const res = await apiFetch(props.fetchUrl);
            if (!res.ok) throw new Error("Failed to load");
            const data = await res.json();
            Object.assign(form, data); console.log("Loaded data:", data);
        }
    } catch (e) {
        error.value = e.message;
    } finally {
        loading.value = false;
    }
}
function initializeForm(schema) {
    schema.sections.forEach(section => {
        (section.fields || []).forEach(field => {
            if (field.type === "password-group") {
                form[field.model] = { password: "", confirm: "" };
            } else {
                form[field.model] = "";
            }
        });
    });
}


function normalizePayload(original) {
    const p = { ...original };

    if (p.password_group) {
        const pass = p.password_group.password || "";
        p.password = pass;
        delete p.password_group;
    }

    return p;
}

// ---- Submit ----
import { validateForm } from "@/utils/validation";

async function submit() {
    error.value = "";
    success.value = "";
    const body = normalizePayload(form);


    // validation
    const errors = validateForm(form, props.schema);
    if (Object.keys(errors).length > 0) {
        validationErrors.value = errors;
        return; // stop submit
    }

    saving.value = true;

    try {
        const res = await apiFetch(props.submitUrl, {
            method: props.method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(form),
        });

        if (!res.ok) throw new Error("Failed to save");

        const data = await res.json();
        success.value = "Saved successfully.";
        emit("saved", data);
    } catch (e) {
        error.value = e.message;
    } finally {
        saving.value = false;
    }
}

</script>
