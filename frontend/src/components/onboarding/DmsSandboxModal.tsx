import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface DmsSandboxModalProps {
  isOpen: boolean;
  stepIndex: number;
  onClose: () => void;
  onSuccess: () => void;
}

export default function DmsSandboxModal({
  isOpen,
  stepIndex,
  onClose,
  onSuccess,
}: DmsSandboxModalProps) {
  // Step 2 (PO & PR) State
  const [poCode, setPoCode] = useState("ZVOR-2026-9901");
  const [itemType, setItemType] = useState("Xe Máy Điện Klara S");
  const [quantity, setQuantity] = useState(5);
  const [prReleased, setPrReleased] = useState(false);

  // Step 3 (Ghép xe & HĐ Pin) State
  const [customerCccd, setCustomerCccd] = useState("001098765432");
  const [vinNumber, setVinNumber] = useState("VFKLARA2026-88192");
  const [contractPrinted, setContractPrinted] = useState(false);

  // Step 4 (Thu tiền & HĐ GTGT) State
  const [voucherCode, setVoucherCode] = useState("VF-PROMO-500K");
  const [voucherApplied, setVoucherApplied] = useState(false);
  const [invoicePushed, setInvoicePushed] = useState(false);

  const [loading, setLoading] = useState(false);
  const [stepComplete, setStepComplete] = useState(false);

  if (!isOpen) return null;

  const handleSimulate = (actionType: string) => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      if (actionType === "pr_release") {
        setPrReleased(true);
        setStepComplete(true);
      } else if (actionType === "print_contract") {
        setContractPrinted(true);
        setStepComplete(true);
      } else if (actionType === "apply_voucher") {
        setVoucherApplied(true);
      } else if (actionType === "push_invoice") {
        setInvoicePushed(true);
        setStepComplete(true);
      }
    }, 800);
  };

  const handleFinish = () => {
    onSuccess();
    onClose();
  };

  return (
    <AnimatePresence>
      <div className="modal-backdrop">
        <motion.div
          className="sandbox-modal"
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
        >
          {/* DMS Header */}
          <div className="dms-header">
            <div className="dms-brand">
              <span className="dms-badge">DMS SIMULATION</span>
              <h3>Phân hệ Mua Hàng & Quản Lý Kho DMS (Môi trường Thử nghiệm)</h3>
            </div>
            <button className="modal-close-btn light" onClick={onClose}>
              ✕
            </button>
          </div>

          {/* DMS Body Content */}
          <div className="dms-body">
            {stepIndex === 1 && (
              /* Step 2: PO & PR Simulation */
              <div className="dms-panel">
                <div className="panel-title">
                  📝 Thao tác Thử: Tạo Đơn hàng (PO) & Phát hành Phiếu nhập kho (PR)
                </div>
                <p className="panel-desc">
                  Thực hành điền thông tin Đơn hàng PO nháp và đổi trạng thái phát hành phiếu PR.
                </p>

                <div className="dms-form-grid">
                  <div className="form-group">
                    <label>Mã Đơn Mua Hàng (PO):</label>
                    <input
                      type="text"
                      value={poCode}
                      onChange={(e) => setPoCode(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label>Loại sản phẩm đặt:</label>
                    <select
                      value={itemType}
                      onChange={(e) => setItemType(e.target.value)}
                    >
                      <option>Xe Máy Điện Klara S</option>
                      <option>Xe Máy Điện Feliz S</option>
                      <option>Xe Máy Điện Vento S</option>
                      <option>Pin LFP 3.5kWh</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Số lượng (Chiếc/Bộ):</label>
                    <input
                      type="number"
                      value={quantity}
                      onChange={(e) => setQuantity(Number(e.target.value))}
                    />
                  </div>

                  <div className="form-group">
                    <label>Trạng thái Phiếu PR:</label>
                    <div
                      className={`status-pill ${
                        prReleased ? "released" : "draft"
                      }`}
                    >
                      {prReleased ? "● ĐÃ PHÁT HÀNH (RELEASED)" : "○ Chưa hành động (Draft)"}
                    </div>
                  </div>
                </div>

                {!prReleased ? (
                  <button
                    className="btn-primary btn-full mt-4"
                    disabled={loading}
                    onClick={() => handleSimulate("pr_release")}
                  >
                    {loading ? "Đang phát hành Phiếu PR..." : "🚀 Phát hành Phiếu Nhập Kho PR"}
                  </button>
                ) : (
                  <div className="alert alert-success mt-4">
                    ✅ Đã phát hành thành công Phiếu Nhập Kho {poCode}! Hàng đã được ghi tăng tồn kho DMS.
                  </div>
                )}
              </div>
            )}

            {stepIndex === 2 && (
              /* Step 3: Ghép xe & HĐ Pin Simulation */
              <div className="dms-panel">
                <div className="panel-title">
                  🚘 Thao tác Thử: Nhập thông tin Khách hàng & Ghép Số khung (VIN)
                </div>

                <div className="dms-form-grid">
                  <div className="form-group">
                    <label>Số CCCD / Định danh Khách hàng:</label>
                    <input
                      type="text"
                      value={customerCccd}
                      onChange={(e) => setCustomerCccd(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label>Số Khung (VIN) ghép tồn kho:</label>
                    <input
                      type="text"
                      value={vinNumber}
                      onChange={(e) => setVinNumber(e.target.value)}
                    />
                  </div>
                </div>

                {!contractPrinted ? (
                  <button
                    className="btn-primary btn-full mt-4"
                    disabled={loading}
                    onClick={() => handleSimulate("print_contract")}
                  >
                    {loading ? "Đang ghép xe & tạo hợp đồng..." : "📄 Ghép Số Khung & In Hợp Đồng Thuê Pin"}
                  </button>
                ) : (
                  <div className="alert alert-success mt-4">
                    ✅ Đã ghép thành công Số khung {vinNumber} cho KH CCCD {customerCccd} & phát hành Hợp đồng thuê Pin!
                  </div>
                )}
              </div>
            )}

            {stepIndex === 3 && (
              /* Step 4: Thu tiền & VNPT Invoice Simulation */
              <div className="dms-panel">
                <div className="panel-title">
                  🧾 Thao tác Thử: Áp mã E-Voucher & Đẩy Hóa đơn GTGT lên VNPT
                </div>

                <div className="dms-form-grid">
                  <div className="form-group">
                    <label>Mã E-Voucher Khuyến mãi:</label>
                    <div className="input-group">
                      <input
                        type="text"
                        value={voucherCode}
                        onChange={(e) => setVoucherCode(e.target.value)}
                      />
                      <button
                        className="btn-outline btn-sm"
                        onClick={() => handleSimulate("apply_voucher")}
                      >
                        {voucherApplied ? "✓ Đã áp" : "Áp dụng"}
                      </button>
                    </div>
                  </div>

                  <div className="form-group">
                    <label>Trạng thái Hóa đơn VNPT:</label>
                    <div className={`status-pill ${invoicePushed ? "released" : "draft"}`}>
                      {invoicePushed ? "● ĐÃ PHÁT HÀNH HÓA ĐƠN GTGT" : "○ Chưa phát hành"}
                    </div>
                  </div>
                </div>

                {!invoicePushed ? (
                  <button
                    className="btn-primary btn-full mt-4"
                    disabled={loading}
                    onClick={() => handleSimulate("push_invoice")}
                  >
                    {loading ? "Đang gửi sang VNPT e-Invoice..." : "⚡ Đẩy Hóa đơn GTGT lên VNPT"}
                  </button>
                ) : (
                  <div className="alert alert-success mt-4">
                    ✅ Hóa đơn GTGT đã được phát hành và ký số thành công trên hệ thống VNPT!
                  </div>
                )}
              </div>
            )}
          </div>

          {/* DMS Footer */}
          <div className="dms-footer">
            <button className="btn-outline" onClick={onClose}>
              Đóng
            </button>
            {stepComplete && (
              <button className="btn-primary" onClick={handleFinish}>
                🎉 Đánh dấu hoàn thành thao tác thử
              </button>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
