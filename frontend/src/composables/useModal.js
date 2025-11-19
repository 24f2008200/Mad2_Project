import { ref, onMounted } from "vue";

export function useModal() {
  const modalEl = ref(null);
  let modalInstance = null;

  onMounted(() => {
    modalInstance = new bootstrap.Modal(modalEl.value);
  });

  const open = () => modalInstance?.show();
  const close = () => modalInstance?.hide();

  return { modalEl, open, close };
}
