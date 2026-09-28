import { Menu, RadioTower } from "lucide-react";

type GovernmentHeaderProps = {
  onMenuClick?: () => void;
};

export default function GovernmentHeader({
  onMenuClick,
}: GovernmentHeaderProps) {
  return (
    <header className="government-header">
      <div className="government-header__left">
        <button
          className="government-header__menu"
          type="button"
          aria-label="Open navigation"
          onClick={onMenuClick}
        >
          <Menu size={21} />
        </button>

        <div className="government-header__context">
          <span className="government-header__eyebrow">
            OPERATIONS CENTER
          </span>
          <h1 className="government-header__title">
            Marine Sonar Intelligence
          </h1>
        </div>
      </div>

      <div className="government-header__right">
        <div className="government-header__system">
          <span className="government-header__system-icon">
            <RadioTower size={16} />
          </span>

          <span className="government-header__system-copy">
            <span className="government-header__system-label">
              PLATFORM
            </span>
            <span className="government-header__system-name">
              DeepSight MVP
            </span>
          </span>
        </div>
      </div>
    </header>
  );
}