import { SnapcastState } from "@/types";
import { INFO_EVENTS } from "../constants";
import { EVENTS } from "@/constants/events";

const initialState: SnapcastState = {
  status: {},
  servers: [],
};

export const snapcastReducer = (state = initialState, action: any): SnapcastState => {
  const { type, payload } = action;

  switch (type) {
    case INFO_EVENTS.SNAPCAST_SCAN_COMPLETED:
      return {
        ...state,
        servers: payload,
      };

    case EVENTS.SNAPCAST_STATE_CHANGED:
      return { ...state, status: payload.server };

    case EVENTS.SNAPCAST_CONNECTED:
    case EVENTS.SNAPCAST_DISCONNECTED:
    case EVENTS.SNAPCAST_REMOVED:
    case EVENTS.SNAPCAST_ADDED:
      return {
        ...state,
        servers: [...state.servers.filter((server) => server?.ip !== payload.server?.ip), payload.server],
      };

    case EVENTS.SNAPCAST_NOTIFICATION: {
      switch (payload.method) {
        case "Stream.OnUpdate": {
          return {
            ...state,
            servers: state.servers.map((server) => (server?.connected ? { ...server, status: payload.params.stream.status } : server)),
          };
        }

        case "Client.OnConnect":
        case "Client.OnDisconnect": {
          const params = payload.params.client;

          const groups: any = state.status?.groups?.map((group: any) => ({
            ...group,
            clients: group.clients?.map((client: any) => (client.id === params.id ? params : client)),
          }));

          return {
            ...state,
            status: {
              ...state.status,
              groups,
            },
          };
        }

        case "Client.OnVolumeChanged": {
          const params = payload.params;

          const groups: any = state.status?.groups?.map((group: any) => ({
            ...group,
            clients: group.clients?.map((client: any) =>
              client.id === params.id
                ? {
                    ...client,
                    config: {
                      ...client.config,
                      volume: { ...params.volume },
                    },
                  }
                : client
            ),
          }));

          return {
            ...state,
            status: {
              ...state.status,
              groups,
            },
          };
        }

        case "Server.OnUpdate": {
          const params = payload.params;
          return {
            ...state,
            status: {
              ...params.server,
            },
          };
        }

        default:
          return state;
      }
    }

    default:
      return state;
  }
};
