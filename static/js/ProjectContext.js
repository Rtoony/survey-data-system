class ProjectContext {
    constructor() {
        if (ProjectContext.instance) {
            return ProjectContext.instance;
        }
        ProjectContext.instance = this;

        this.activeProject = null;
        this.projectList = [];
        this.isInitialized = false;
        this.initPromise = null;
        this.listeners = [];

        window.addEventListener('storage', (e) => {
            if (e.key === 'last_active_project_id' && e.newValue !== e.oldValue) {
                this.refreshActiveProject();
            }
        });
    }

    async init() {
        if (this.isInitialized) {
            return this.activeProject;
        }

        if (this.initPromise) {
            return this.initPromise;
        }

        this.initPromise = this._doInit();
        return this.initPromise;
    }

    async _doInit() {
        try {
            await this.fetchProjectList();
            await this.fetchActiveProject();

            this.isInitialized = true;
            return this.activeProject;
        } catch (error) {
            console.error('Error initializing ProjectContext:', error);
            throw error;
        }
    }

    async fetchActiveProject() {
        try {
            const response = await fetch('/api/active-project');
            const data = await response.json();

            this.activeProject = data.active_project;

            if (this.activeProject) {
                localStorage.setItem('last_active_project_id', this.activeProject.project_id);
            } else {
                const lastProjectId = localStorage.getItem('last_active_project_id');
                if (lastProjectId && this.projectList.length > 0) {
                    const lastProject = this.projectList.find(p => p.project_id === lastProjectId);
                    if (lastProject) {
                        await this.setActiveProject(lastProjectId, false);
                    }
                }
            }

            return this.activeProject;
        } catch (error) {
            console.error('Error fetching active project:', error);
            return null;
        }
    }

    async fetchProjectList() {
        try {
            const response = await fetch('/api/projects');
            const data = await response.json();
            this.projectList = data.projects || [];
            return this.projectList;
        } catch (error) {
            console.error('Error fetching project list:', error);
            this.projectList = [];
            return [];
        }
    }

    async setActiveProject(projectId, emitEvent = true) {
        try {
            const response = await fetch('/api/active-project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ project_id: projectId })
            });

            if (!response.ok) {
                throw new Error('Failed to set active project');
            }

            const data = await response.json();
            const previousProject = this.activeProject;
            this.activeProject = data.active_project;

            if (this.activeProject) {
                localStorage.setItem('last_active_project_id', this.activeProject.project_id);
            } else {
                localStorage.removeItem('last_active_project_id');
            }

            if (emitEvent) {
                this.emitProjectChange(previousProject, this.activeProject);
            }

            return this.activeProject;
        } catch (error) {
            console.error('Error setting active project:', error);
            this.showNotification('Failed to set active project', 'error');
            throw error;
        }
    }

    async clearActiveProject() {
        return this.setActiveProject(null);
    }

    async refreshActiveProject() {
        const previousProject = this.activeProject;
        await this.fetchActiveProject();
        
        if (previousProject?.project_id !== this.activeProject?.project_id) {
            this.emitProjectChange(previousProject, this.activeProject);
        }
    }

    onProjectChange(callback) {
        this.listeners.push(callback);
        
        return () => {
            this.listeners = this.listeners.filter(cb => cb !== callback);
        };
    }

    emitProjectChange(previousProject, newProject) {
        const event = new CustomEvent('project-change', {
            detail: {
                previous: previousProject,
                current: newProject
            }
        });
        window.dispatchEvent(event);

        this.listeners.forEach(callback => {
            try {
                callback(newProject, previousProject);
            } catch (error) {
                console.error('Error in project change listener:', error);
            }
        });
    }

    getActiveProject() {
        return this.activeProject;
    }

    getProjectList() {
        return this.projectList;
    }

    hasActiveProject() {
        return this.activeProject !== null;
    }

    showNotification(message, type = 'info') {
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            const event = new CustomEvent('app-notification', {
                detail: { message, type }
            });
            window.dispatchEvent(event);
        }
    }
}

const projectContext = new ProjectContext();
window.projectContext = projectContext;
