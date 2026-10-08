import { registry } from "@web/core/registry";
import { LoginScreen as PosLoginScreen } from "@point_of_sale/app/screens/login_screen/login_screen";
import { _t } from "@web/core/l10n/translation";

export class ChebuLoginScreen extends PosLoginScreen {
    setup() {
        super.setup();
        this.chebuRegisters = [];
        this.selectedRegisterId = null;
        this.loadingRegisters = true;
        this.loadRegisters();
    }

    async loadRegisters() {
        try {
            const registers = await this.pos.data.call(
                "chebu.pos.register",
                "get_registers_for_pos",
                []
            );
            this.chebuRegisters = registers || [];
            const requestedRegisterId = Number(
                new URLSearchParams(window.location.search).get("chebu_register_id")
            );
            const requestedRegister = this.chebuRegisters.find(
                (register) => register.id === requestedRegisterId
            );
            const canResumeRequested =
                requestedRegister &&
                (requestedRegister.status === "available" ||
                    (requestedRegister.status === "active" &&
                        requestedRegister.user_id === this.pos.user.id));
            if (canResumeRequested) {
                this.selectedRegisterId = requestedRegister.id;
            } else if (this.chebuRegisters.length) {
                const available = this.chebuRegisters.find(
                    (register) => register.status === "available"
                );
                this.selectedRegisterId = available ? available.id : this.chebuRegisters[0].id;
            } else {
                this.selectedRegisterId = null;
            }
        } catch (error) {
            this.chebuRegisters = [];
            this.pos.notification.add(
                _t("Chebu register data could not be loaded."),
                { type: "danger" }
            );
        } finally {
            this.loadingRegisters = false;
        }
    }

    get selectedRegister() {
        return (
            this.chebuRegisters.find((register) => register.id === this.selectedRegisterId) || null
        );
    }

    canUseRegister(register) {
        return (
            register.status === "available" ||
            (register.status === "active" && register.user_id === this.pos.user.id)
        );
    }

    selectRegister(register) {
        if (!this.canUseRegister(register)) {
            this.pos.notification.add(_t("Register already in use."), { type: "danger" });
            return;
        }
        this.selectedRegisterId = register.id;
    }

    async openRegister() {
        if (!this.selectedRegisterId) {
            this.pos.notification.add(
                _t("Please select a register before opening it."),
                { type: "danger" }
            );
            return;
        }

        const chosen = this.chebuRegisters.find(
            (register) => register.id === this.selectedRegisterId
        );
        if (!chosen) {
            this.pos.notification.add(
                _t("Selected register is no longer available."),
                { type: "danger" }
            );
            return;
        }
        if (!this.canUseRegister(chosen)) {
            this.pos.notification.add(_t("Register already in use."), { type: "danger" });
            return;
        }

        try {
            const response = await this.pos.data.call("chebu.pos.register", "claim_register", [
                chosen.id,
                this.pos.user.id,
                this.pos.session?.id || false,
            ]);
            if (!response || !response.success) {
                this.pos.notification.add(
                    _t("Your POS session could not be opened."),
                    { type: "danger" }
                );
                return;
            }
            this.pos.chebu_register = response.register;
            this.selectOneCashier(this.pos.user);
        } catch (error) {
            const message =
                error && error.message
                    ? error.message
                    : _t("Your POS session could not be opened.");
            this.pos.notification.add(message, { type: "danger" });
        }
    }
}

registry.category("pos_screens").add("LoginScreen", ChebuLoginScreen, { force: true });
