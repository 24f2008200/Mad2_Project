import { defineStore } from "pinia";
import { ref } from "vue";

export const useSearchStore = defineStore("search", () => {
  // state
  const searchType = ref("user");     // default
  const searchBy = ref("");
  const searchValue = ref("");   // default
  const navbarAction = ref(null);     // will hold a function
  const searchAction = ref(null);
  const startDate = ref(null);
  const endDate = ref(null);
  const opCode = ref(null);

  // actions
  function setSearchType(type) {
    searchType.value = type;
  }
  
  function setOpCode(nCode) {
    opCode.value = nCode;
  }

  function setStartDate(date) {
    startDate.value = date;
  }
  function setEndDate(date) {
    endDate.value = date;
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
    if (navbarAction.value) { console.log("Triggering navbar action");
      navbarAction.value();
    } else {

    }
  }
  function triggerSearchAction() {console.log("Triggering search action");
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
    startDate,
    endDate,
    opCode,
    setOpCode,
    setStartDate,
    setEndDate,
    setSearchType,
    setSearchValue,
    setNavbarAction,
    setFetchAction,
    triggerNavbarAction,
    triggerSearchAction
  };
});
