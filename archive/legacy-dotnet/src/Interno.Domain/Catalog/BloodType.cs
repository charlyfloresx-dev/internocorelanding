using System.ComponentModel.DataAnnotations;

namespace Interno.Domain.Catalog
{
    public class BloodType {
        [Key]
        [MaxLength (3)]
        public string Group { get; set; }
        public virtual string Donate { get; set; }
        public virtual string Receive { get; set; }

        /*
        'A+': {donate:'A+ AB+',                      receive:'A+ A- O+ O-'}
        'A-': {donate:'A+ A- AB+ AB-',               receive:'A- O-'
        'AB+':{donate:'AB+',                         receive:'A+ O+ B+ AB+ A- O- B- AB-'
        'AB-':{donate:'AB+ AB-',                     receive:'AB- A- B- O-'
        'B+': {donate:'B+ AB+',                      receive:'B+ B- O+ O-'
        'B-': {donate:'B+ B- AB+ AB-',               receive:'B- O-'
        'O+': {donate:'O+ A+ B+ AB+',                receive:'O+ O-'
        'O-': {donate:'A+ O+ B+ AB+ A- O- B- AB-',   receive:'O-'
    */
    }
}