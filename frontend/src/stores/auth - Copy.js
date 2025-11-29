import { ref, computed } from 'vue';

const token = ref(localStorage.getItem('access_token'));
const isAdmin = ref(localStorage.getItem('is_admin') === 'true');
const userName = ref(localStorage.getItem('user_name') || '');
const userId = ref(localStorage.getItem('user_id') || '');

export function useAuthStore() {
  const isLoggedIn = computed(() => token.value !== null);

  function login(data) {
 
    token.value = data.access_token;
    isAdmin.value = data.user.is_admin;
    userName.value = data.user.name;
    userId.value = data.user.id;

    // persist to localStorage 
    localStorage.setItem('access_token', token.value);
    localStorage.setItem('is_admin', isAdmin.value);
    localStorage.setItem('user_name', userName.value);
    localStorage.setItem('user_id', userId.value);
  }

  function logout() {
    token.value = null;
    isAdmin.value = false;
    userName.value = '';
    userId.value = '';

    // clear from localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('is_admin');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_id');
  } 

  return { token, isAdmin, userName, userId, isLoggedIn, login, logout };
}
