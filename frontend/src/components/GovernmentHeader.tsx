export default function GovernmentHeader() {
    return (
        <header className="government-header">
            <div className="government-header__inner">
                <div className="government-header__brand">
                    <div className="government-header__icon">
                        <SonarEmblem />
                    </div>

                    <div className="government-header__text">
                        <h1>Marine Sonar Intelligence Platform</h1>
                    </div>
                </div>
            </div>
        </header>
    )
}

function SonarEmblem() {
    return (
        <svg
            viewBox="0 0 64 64"
            className="government-header__emblem"
            aria-hidden="true"
        >
            <circle cx="32" cy="32" r="29" fill="#fffaf2" />
            <circle
                cx="32"
                cy="32"
                r="27"
                fill="none"
                stroke="#d6a96a"
                strokeWidth="1.5"
            />
            <path
                d="M32 15v34"
                stroke="#8d3b22"
                strokeWidth="2"
                strokeLinecap="round"
            />
            <path
                d="M21 28c4-7 8-10 11-10s7 3 11 10"
                fill="none"
                stroke="#8d3b22"
                strokeWidth="2"
                strokeLinecap="round"
            />
            <path
                d="M24 34c3-4 6-6 8-6s5 2 8 6"
                fill="none"
                stroke="#8d3b22"
                strokeWidth="2"
                strokeLinecap="round"
            />
            <path
                d="M20 40c4-3 8-4 12-4s8 1 12 4"
                fill="none"
                stroke="#8d3b22"
                strokeWidth="2"
                strokeLinecap="round"
            />
            <circle cx="32" cy="32" r="2.5" fill="#8d3b22" />
        </svg>
    )
}
