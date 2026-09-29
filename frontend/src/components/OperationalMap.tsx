import {
    CircleMarker,
    MapContainer,
    Popup,
    TileLayer,
} from "react-leaflet"

import type { DetectionReview } from "../types/api"

import "leaflet/dist/leaflet.css"
import "./OperationalMap.css"

const DEFAULT_CENTER: [number, number] = [20, 0]

function hasCoordinates(
    review: DetectionReview,
): review is DetectionReview & {
    latitude: number
    longitude: number
} {
    return (
        review.latitude !== null &&
        review.longitude !== null &&
        Number.isFinite(review.latitude) &&
        Number.isFinite(review.longitude)
    )
}

export default function OperationalMap({
    reviews,
}: {
    reviews: DetectionReview[]
}) {
    const locatedReviews = reviews.filter(hasCoordinates)

    return (
        <section className="operational-map">
            <div className="operational-map__header">
                <div>
                    <span className="operational-map__eyebrow">
                        GEOSPATIAL VIEW
                    </span>

                    <h3>Detection Locations</h3>

                    <p>
                        Only usable coordinates from persisted
                        sonar metadata are plotted.
                    </p>
                </div>

                <span className="operational-map__count">
                    {locatedReviews.length} located
                </span>
            </div>

            <div className="operational-map__body">
                <MapContainer
                    center={DEFAULT_CENTER}
                    zoom={2}
                    scrollWheelZoom
                    className="operational-map__canvas"
                >
                    <TileLayer
                        attribution='&copy; OpenStreetMap contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    {locatedReviews.map((review) => (
                        <CircleMarker
                            key={review.id}
                            center={[
                                review.latitude,
                                review.longitude,
                            ]}
                            radius={8}
                            pathOptions={{
                                color: "#8d3b22",
                                fillColor: "#c27b3c",
                                fillOpacity: 0.85,
                                weight: 2,
                            }}
                        >
                            <Popup>
                                <strong>
                                    {review.class_name}
                                </strong>

                                <br />

                                Detection #
                                {review.detection_id}

                                <br />

                                Confidence:{" "}
                                {(review.confidence * 100).toFixed(
                                    1,
                                )}
                                %

                                <br />

                                Lat:{" "}
                                {review.latitude.toFixed(6)}

                                <br />

                                Lon:{" "}
                                {review.longitude.toFixed(6)}

                                <br />

                                Metadata verified:{" "}
                                {review.metadata_verified
                                    ? "Yes"
                                    : "No"}
                            </Popup>
                        </CircleMarker>
                    ))}
                </MapContainer>

                {locatedReviews.length === 0 && (
                    <div className="operational-map__empty">
                        <strong>
                            Location unavailable
                        </strong>

                        <span>
                            No persisted detection in this
                            view contains usable latitude
                            and longitude metadata.
                        </span>
                    </div>
                )}
            </div>
        </section>
    )
}
