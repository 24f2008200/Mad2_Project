import { defineStore } from "pinia";
import { ref } from "vue";

export const useSearchStore = defineStore("search", () => {
  // state
  const searchType = ref("user");     // default
  const searchBy = ref("");
  const searchValue = ref("");   // default
  const navbarAction = ref(null);     // will hold a function
  const searchAction = ref(null);
  // actions
  function setSearchType(type) {
    searchType.value = type;
  }

  function setSearchValue(nValue) {
    searchValue.value = nValue;
  }

  function setFetchAction(nValue) {

    searchAction.value = nValue;
  }

  function setNavbarAction(actionFn) {

    navbarAction.value = actionFn;
  }

  function triggerNavbarAction() {
    if (navbarAction.value) {
      navbarAction.value();
    } else {

    }
  }
  function triggerSearchAction() {
    if (searchAction.value) {
      searchAction.value();
    } else {

    }
  }

  // expose
  return {
    searchType,
    searchBy,
    searchValue,
    navbarAction,
    searchAction,
    setSearchType,
    setSearchValue,
    setNavbarAction,
    setFetchAction,
    triggerNavbarAction,
    triggerSearchAction
  };
});
