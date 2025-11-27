import React from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons for different stop types
const createCustomIcon = (color) => {
    return new L.Icon({
        iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
};

const stopIcons = {
    'PICKUP': createCustomIcon('green'),
    'DROPOFF': createCustomIcon('red'),
    'FUEL': createCustomIcon('orange'),
    'REST': createCustomIcon('blue'),
    'OVERNIGHT': createCustomIcon('violet')
};

const RouteMap = ({ stops, routeCoordinates }) => {
    // Default center (US center) if no coordinates
    const defaultCenter = [39.8283, -98.5795];

    // Calculate map center based on route
    const calculateCenter = () => {
        if (routeCoordinates && routeCoordinates.length > 0) {
            const lats = routeCoordinates.map(coord => coord[1]);
            const lngs = routeCoordinates.map(coord => coord[0]);
            return [
                (Math.min(...lats) + Math.max(...lats)) / 2,
                (Math.min(...lngs) + Math.max(...lngs)) / 2
            ];
        }
        return defaultCenter;
    };

    // Convert coordinates for Leaflet [lat, lng] format
    const convertCoordinates = (coords) => {
        if (!coords || coords.length === 0) return [];
        return coords.map(coord => [coord[1], coord[0]]); // Convert [lng, lat] to [lat, lng]
    };

    // Estimate stop positions along the route
    // In RouteMap.js - improve getStopPositions function
    const getStopPositions = () => {
        if (!routeCoordinates || routeCoordinates.length === 0) return [];

        return stops.map(stop => {
            if (stop.distance === 0) {
                return routeCoordinates[0]; // Start
            }

            // Find the closest point on the route based on accumulated distance
            let accumulatedDistance = 0;
            for (let i = 1; i < routeCoordinates.length; i++) {
                const prevCoord = routeCoordinates[i - 1];
                const currCoord = routeCoordinates[i];
                const segmentDistance = calculateDistance(prevCoord, currCoord);

                if (accumulatedDistance + segmentDistance >= stop.distance * 1000) { // Convert to meters
                    // Interpolate position along this segment
                    const fraction = (stop.distance * 1000 - accumulatedDistance) / segmentDistance;
                    const lng = prevCoord[0] + (currCoord[0] - prevCoord[0]) * fraction;
                    const lat = prevCoord[1] + (currCoord[1] - prevCoord[1]) * fraction;
                    return [lng, lat];
                }
                accumulatedDistance += segmentDistance;
            }

            // Fallback to end of route
            return routeCoordinates[routeCoordinates.length - 1];
        });
    };

    // Helper function to calculate distance between two coordinates
    // const calculateDistance = (coord1, coord2) => {
    //     const [lng1, lat1] = coord1;
    //     const [lng2, lat2] = coord2;

    //     const R = 6371000; // Earth radius in meters
    //     const dLat = (lat2 - lat1) * Math.PI / 180;
    //     const dLng = (lng2 - lng1) * Math.PI / 180;
    //     const a =
    //         Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    //         Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    //         Math.sin(dLng / 2) * Math.sin(dLng / 2);
    //     const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    //     return R * c;
    // };

    const calculateDistance = (coord1, coord2) => {
        const [lng1, lat1] = coord1;
        const [lng2, lat2] = coord2;

        const R = 6371000; // Earth radius in meters
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLng = (lng2 - lng1) * Math.PI / 180;
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLng / 2) * Math.sin(dLng / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    };

    const mapCenter = calculateCenter();
    const polylinePositions = convertCoordinates(routeCoordinates);
    const stopPositions = getStopPositions();

    return (
        <MapContainer
            center={mapCenter}
            zoom={5}
            style={{ height: '400px', width: '100%', borderRadius: '8px' }}
            scrollWheelZoom={true}
        >
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Route Polyline */}
            {polylinePositions.length > 0 && (
                <Polyline
                    positions={polylinePositions}
                    color="blue"
                    weight={4}
                    opacity={0.7}
                />
            )}

            {/* Stop Markers */}
            {stops.map((stop, index) => {
                if (index >= stopPositions.length) return null;

                const position = stopPositions[index];
                if (!position) return null;

                const convertedPosition = [position[1], position[0]]; // Convert to [lat, lng]

                return (
                    <Marker
                        key={index}
                        position={convertedPosition}
                        icon={stopIcons[stop.type] || stopIcons.PICKUP}
                    >
                        <Popup>
                            <div>
                                <strong>{stop.type}</strong>
                                <br />
                                {stop.location}
                                <br />
                                Distance: {stop.distance} km
                                <br />
                                Stop: {stop.stop_duration}h
                            </div>
                        </Popup>
                    </Marker>
                );
            })}
        </MapContainer>
    );
};

export default RouteMap;