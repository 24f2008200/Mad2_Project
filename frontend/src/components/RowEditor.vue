<template>
    <div class="p-3">
        <h5 class="mb-3">{{ title }}</h5>

        <form @submit.prevent="onSave">
            <div class="row g-3"> <!-- add gutter spacing -->
                <div v-for="field in fields" :key="field.key" class="col-md-6">
                    <div v-if="field.type !== 'action'">
                        <label class="form-label">{{ field.label }}</label>

                        <!-- Input types -->
                        <input v-if="field.type === 'text'" v-model="localRow[field.key]" type="text"
                            class="form-control" />

                        <div v-else-if="field.type === 'noedit'" class="form-control-plaintext">
                            {{ localRow[field.key] }}
                        </div>

                        <input v-else-if="field.type === 'number'" v-model.number="localRow[field.key]" type="number"
                            class="form-control" />

                        <input v-else-if="field.type === 'email'" v-model="localRow[field.key]" type="email"
                            class="form-control" />

                        <select v-else-if="field.type === 'select'" v-model="localRow[field.key]" class="form-select">
                            <option v-for="opt in field.options" :key="opt" :value="opt">
                                {{ opt }}
                            </option>
                        </select>

                        <!-- fallback text -->
                        <input v-else v-model="localRow[field.key]" type="text" class="form-control" />
                    </div>
                </div>
            </div>

            <!-- Action buttons -->
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
import { reactive, watch, watchEffect } from "vue"

const props = defineProps({
    row: { type: Object, required: true },   // initial row
    fields: { type: Array, required: true }, // list of fields with { key, label, type, options? }
    title: { type: String, default: "Edit Record" }
})

const emit = defineEmits(["save", "cancel"])
const localRow = reactive({ ...props.row })

// function parseDateTime(val) {
//   if (!val) return { date: "", time: "" }
//   const d = new Date(val)
//   if (isNaN(d)) return { date: "", time: "" }

//   const yyyy = d.getFullYear()
//   const mm = String(d.getMonth() + 1).padStart(2, "0")
//   const dd = String(d.getDate()).padStart(2, "0")
//   const hh = String(d.getHours()).padStart(2, "0")
//   const min = String(d.getMinutes()).padStart(2, "0")

//   return {
//     date: `${yyyy}-${mm}-${dd}`,
//     time: `${hh}:${min}`
//   }
// }
watchEffect(() => {
    const newRow = props.row
    if (!newRow) return
    Object.assign(localRow, newRow)
    //   props.fields.forEach(f => {
    //     if (f.type === "datetime" && newRow[f.key]) {
    //       const { date, time } = parseDateTime(newRow[f.key])
    //       localRow[f.key + "_date"] = date
    //       localRow[f.key + "_time"] = time
    //     }
    //   })
})

function onSave() {
    const output = { ...localRow }

    // recombine datetime fields
    //   props.fields.forEach(f => {
    //     if (f.type === "datetime") {
    //       const d = output[f.key + "_date"]
    //       const t = output[f.key + "_time"]
    //       if (d && t) {
    //         output[f.key] = `${d}T${t}:00` // local datetime
    //       }
    //       delete output[f.key + "_date"]
    //       delete output[f.key + "_time"]
    //     }
    //   })

    emit("save", output)
}
</script>