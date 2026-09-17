export type MediaType = 'anime' | 'manga' | 'light_novel';

export interface MediaConfig {
  title: string;
  type: MediaType;
  primaryColor: string;
  apiPath: string;
  unitLabel: string;
  supportsMovies: boolean;
}

export const getMediaConfig = (type: MediaType): MediaConfig => {
  switch (type) {
    case 'anime':
      return {
        title: 'Animes',
        type: 'anime',
        primaryColor: 'text-blue-500',
        apiPath: '/api/media/anime',
        unitLabel: 'Episódio',
        supportsMovies: true,
      };
    case 'manga':
      return {
        title: 'Mangás',
        type: 'manga',
        primaryColor: 'text-orange-500',
        apiPath: '/api/media/manga',
        unitLabel: 'Capítulo',
        supportsMovies: false,
      };
    case 'light_novel':
      return {
        title: 'Light Novels',
        type: 'light_novel',
        primaryColor: 'text-purple-500',
        apiPath: '/api/media/light_novel',
        unitLabel: 'Capítulo',
        supportsMovies: false,
      };
    default:
      throw new Error(`Unsupported media type: ${type}`);
  }
};
