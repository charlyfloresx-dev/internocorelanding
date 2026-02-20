namespace Interno.Hotel.Models
{
    public class Room
    {

        public int Id { get; set; }
        public string Number { get; set; }
        public RoomStatus Status { get; set; }
        public string Url { get; set; }
        public string Description { get; set; }

    }
}