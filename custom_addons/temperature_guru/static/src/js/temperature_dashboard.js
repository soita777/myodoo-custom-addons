/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class TemperatureGuruDashboard extends Component {
    static template = "temperature_guru.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            error: null,
            branchId: "all",
            data: null,
        });
        onWillStart(() => this.loadDashboard());
    }

    async loadDashboard() {
        this.state.loading = true;
        this.state.error = null;
        try {
            this.state.data = await this.orm.call(
                "temperature.guru.dashboard",
                "get_dashboard_data",
                [this.state.branchId === "all" ? false : Number(this.state.branchId)]
            );
        } catch (error) {
            this.state.error = error.message || "Temperature data could not be loaded.";
        } finally {
            this.state.loading = false;
        }
    }

    onBranchChange(event) {
        this.state.branchId = event.target.value;
        this.loadDashboard();
    }

    refresh() {
        this.loadDashboard();
    }

    openDevices() {
        return this.action.doAction("temperature_guru.action_temperature_guru_devices");
    }

    openReadings() {
        return this.action.doAction("temperature_guru.action_temperature_guru_readings");
    }

    addDevice() {
        return this.action.doAction("temperature_guru.action_temperature_guru_new_device", {
            additionalContext: { default_branch_id: this.state.branchId === "all" ? false : Number(this.state.branchId) },
        });
    }

    logReading(deviceId, branchId) {
        return this.action.doAction("temperature_guru.action_temperature_guru_new_reading", {
            additionalContext: { default_device_id: deviceId, default_branch_id: branchId },
        });
    }

    statusLabel(status) {
        return {
            normal: "In range",
            low: "Too cold",
            high: "Too warm",
            offline: "No recent reading",
            no_data: "Awaiting reading",
            maintenance: "Maintenance",
            inactive: "Inactive",
        }[status] || status;
    }

    formatTemperature(value) {
        return typeof value === "number" ? `${value.toFixed(1)} °C` : "No reading";
    }

    formatDate(value) {
        if (!value) {
            return "Never";
        }
        const date = new Date(`${value.replace(" ", "T")}Z`);
        return new Intl.DateTimeFormat(undefined, {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        }).format(date);
    }

    sparkline(values) {
        if (!values || values.length < 2) {
            return "M 0 22 L 100 22";
        }
        const min = Math.min(...values);
        const max = Math.max(...values);
        const spread = max - min || 1;
        return values
            .map((value, index) => {
                const x = (index / (values.length - 1)) * 100;
                const y = 38 - ((value - min) / spread) * 30;
                return `${index ? "L" : "M"} ${x.toFixed(1)} ${y.toFixed(1)}`;
            })
            .join(" ");
    }

    branchBarWidth(branch) {
        const values = (this.state.data?.branches || [])
            .map((item) => item.average)
            .filter((value) => typeof value === "number");
        const max = Math.max(...values, 1);
        return Math.max(3, Math.min(100, (branch.average / max) * 100));
    }
}

registry.category("actions").add("temperature_guru.dashboard", TemperatureGuruDashboard);