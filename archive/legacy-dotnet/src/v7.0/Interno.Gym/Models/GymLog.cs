namespace Interno.Gym
{
    public class GymLog
    {
        public int Id { get; set; }
        public DateTime DateTime { get; set; }
        public int PartnerId { get; set; }
        public Partner Partner { get; set; }
    }
}