/**
 * Created by jaywoods on 2017/6/24.
 */
import { action, computed, get, observable, set } from 'mobx';
import axios from '../components/axios';
import AppState from './AppState';

const BATCH_SIZE = 30;

function getMenuType(menuType = AppState.currentMenuType, isUser = AppState.isTypeUser) {
  return isUser ? 'user' : menuType.type;
}

function filterEmptyMenus(menuData, parent) {
  const newMenuData = menuData.filter((item) => {
    const { name, type, subMenus } = item;
    return name !== null && (type === 'menu' || (subMenus !== null && filterEmptyMenus(subMenus, item).length > 0));
  });
  if (parent) {
    parent.subMenus = newMenuData;
  }
  return newMenuData;
}

class MenuStore {
  @observable menuGroup = {
    site: [],
    user: [],
    organization: {},
    project: {},
  };

  @observable collapsed = false;

  @observable activeMenu = null;

  @observable selected = null;

  @observable leftOpenKeys = [];

  @observable openKeys = [];

  @observable type = null;

  @observable isUser = null;

  @observable id = null;

  statistics = {};

  counter = 0;

  click(code, level, name) {
    if (level in this.statistics) {
      if (code in this.statistics[level]) {
        this.statistics[level][code].count += 1;
      } else {
        this.statistics[level][code] = { count: 1, name };
      }
    } else {
      this.statistics[level] = {};
      this.statistics[level][code] = { count: 1, name };
    }
    this.counter += 1;
    const postData = Object.keys(this.statistics).map(type => ({ level: type, menus: Object.keys(this.statistics[type]).map(mCode => ({ mCode, ...this.statistics[type][mCode] })) }));
    if (postData.reduce((p, cur) => p + cur.menus.reduce((menusP, menusCur) => menusP + menusCur.count, 0), 0) >= BATCH_SIZE) {
      this.uploadStatistics();
      this.counter = 0;
    }
    localStorage.setItem('rawStatistics', JSON.stringify(this.statistics));
  }

  uploadStatistics() {
    const postData = Object.keys(this.statistics).map(type => ({ level: type, menus: Object.keys(this.statistics[type]).map(code => ({ code, ...this.statistics[type][code] })) }));
    axios.post('/manager/v1/statistic/menu_click/save', JSON.stringify(postData)).then((data) => {
      if (!data.failed) {
        this.statistics = {};
      }
    });
  }

  @action
  setCollapsed(collapsed) {
    this.collapsed = collapsed;
  }

  @action
  setActiveMenu(activeMenu) {
    this.activeMenu = activeMenu;
  }

  @action
  setSelected(selected) {
    this.selected = selected;
  }

  @action
  setLeftOpenKeys(leftOpenKeys) {
    this.leftOpenKeys = leftOpenKeys;
  }

  @action
  setOpenKeys(openKeys) {
    this.openKeys = openKeys;
  }

  @action
  setType(type) {
    this.type = type;
  }

  @action
  setIsUser(isUser) {
    this.isUser = isUser;
  }

  @action
  setId(id) {
    this.id = id;
  }

  @action
  loadMenuData(menuType = AppState.currentMenuType, isUser) {
    const type = getMenuType(menuType, isUser) || 'site';
    const { id = 0 } = menuType;
    const menu = this.menuData(type, id);
    if (menu.length) {
      return Promise.resolve(menu);
    }
    return axios.get(`/iam/v1/menus?level=${type}&source_id=${id}`).then(action((data) => {
      const child = filterEmptyMenus(data);
      this.setMenuData(child, type, id);
      return child;
    }));
  }

  @action
  setMenuData(child, childType, id = AppState.currentMenuType.id) {
    const data = filterEmptyMenus(child);
    if (id) {
      set(this.menuGroup[childType], id, data);
    } else {
      set(this.menuGroup, childType, data);
    }
  }

  @computed
  get getMenuData() {
    return this.menuData();
  }

  @computed
  get getSiteMenuData() {
    return this.menuData('site', 0);
  }

  menuData(type = getMenuType(), id = AppState.currentMenuType.id) {
    let data;
    if (type) {
      if (id) {
        data = get(this.menuGroup[type], id);
      } else {
        data = get(this.menuGroup, type);
      }
    }
    return data || [];
  }

  treeReduce(tree, callback, childrenName = 'subMenus', parents = []) {
    if (tree.code) {
      parents.push(tree);
    }
    return tree[childrenName].some((node, index) => {
      const newParents = parents.slice(0);
      if (node[childrenName] && node[childrenName].length > 0) {
        return this.treeReduce(node, callback, childrenName, newParents);
      }
      node.parentName = parents[0].name;
      return callback(node, parents, index);
    });
  }
}

const menuStore = new MenuStore();

export default menuStore;
